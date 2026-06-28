import streamlit as st
import json
from supabase import create_client
# supabase_logic.py ထဲမှာ ဒီလိုဖြစ်နေရပါမယ်
from datetime import datetime
import pytz

def get_myanmar_time():
    myanmar_tz = pytz.timezone('Asia/Yangon')
    return datetime.now(myanmar_tz)

# insert_sale_to_supabase ထဲမှာ
data = {
    # ...
    "created_at": get_myanmar_time().isoformat(), # ဒီနေရာမှာ မြန်မာအချိန်ကို သိမ်းတာပါ
    # ...
}
# ==========================================
# 1. Connection Initialization
# ==========================================
@st.cache_resource
def _get_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

supabase = _get_client()

# ဥပမာ - Product update လုပ်တဲ့နေရာမှာသာ ခေါ်ပါ
def update_product_stock(barcode, new_stock):
    if not supabase: return
    supabase.table("products").update({"stock_qty": int(new_stock)}).eq("barcode", barcode).execute()
    # ဒီနေရာမှာပဲ ခေါ်ပါ၊ တခြားနေရာမှာ မခေါ်ပါနဲ့
    st.cache_data.clear()

# ==========================================
# 2. Sale & Sync Functions
# ==========================================
def insert_sale_to_supabase(cart, totals, receipt_no, payment_method, customer_name):
    if not supabase: raise Exception("Database Connection မရှိပါ။")
    data = {
        "receipt_no": receipt_no,
        "customer_name": customer_name,
        "grand_total": float(totals.get("grand_total", 0)),
        "payment_type": payment_method,
        "created_at": datetime.now().isoformat(),
        "item": json.dumps(cart, ensure_ascii=False),
        "totals": json.dumps(totals, ensure_ascii=False)
    }
    return supabase.table("sales").insert(data).execute()

def sync_to_supabase():
    if "pending_sales" not in st.session_state or not st.session_state.pending_sales:
        return
    for sale in list(st.session_state.pending_sales):
        try:
            insert_sale_to_supabase(sale['cart'], sale['totals'], sale['rec_no'], sale['payment_method'], sale['customer'])
            st.session_state.pending_sales.remove(sale)
        except Exception as e:
            st.error(f"Syncing error: {e}")
            raise e

# ==========================================
# 3. Product & Stock Management
# ==========================================
@st.cache_data(ttl=600)
def get_products_cached():
    if not supabase: return []
    try:
        response = supabase.table("products").select("*").execute()
        return response.data if response.data else []
    except Exception: return []

def find_by_barcode(barcode):
    products = get_products_cached()
    return next((p for p in products if str(p.get("barcode")) == str(barcode)), None)

def update_product_stock(barcode, new_stock):
    if not supabase: return
    supabase.table("products").update({"stock_qty": int(new_stock)}).eq("barcode", barcode).execute()
    _clear_cache()

def process_sale_stock_update(cart):
    for item in cart:
        barcode = str(item.get("barcode"))
        product = find_by_barcode(barcode)
        if product:
            new_stock = int(product.get("stock_qty", 0)) - int(item.get("qty", 0))
            update_product_stock(barcode, new_stock)

# ==========================================
# 4. Refund Functions (အသစ်ထည့်သွင်းခြင်း)
# ==========================================
def log_refund(receipt_no, items, total_refunded):
    if not supabase: return
    log_data = {
        "receipt_no": receipt_no,
        "details": f"Refunded {len(items)} items",
        "amount": float(total_refunded),
        "timestamp": datetime.now().isoformat()
    }
    supabase.table("refund_logs").insert(log_data).execute()

def execute_refund(inv, items_to_refund):
    if not supabase: return 0
    total_refunded = 0
    for item in items_to_refund:
        barcode = str(item.get('barcode'))
        qty = int(item.get('qty', 0))
        # Stock ပြန်တိုးခြင်း
        product = find_by_barcode(barcode)
        if product:
            new_stock = int(product.get("stock_qty", 0)) + qty
            update_product_stock(barcode, new_stock)
        price = float(item.get('sell_price') or item.get('price') or 0)
        total_refunded += (price * qty)
    
    refund_data = {
        "receipt_no": inv.get('receipt_no'),
        "items": json.dumps(items_to_refund, ensure_ascii=False),
        "refund_amount": float(total_refunded),
        "refunded_at": datetime.now().isoformat()
    }
    supabase.table("refunds").insert(refund_data).execute()
    log_refund(inv.get('receipt_no'), items_to_refund, total_refunded)
    return total_refunded
