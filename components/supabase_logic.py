import streamlit as st
import json
from supabase import create_client
from datetime import datetime
import pytz

# ==========================================
# 0. Helper Functions
# ==========================================
def get_myanmar_time():
    myanmar_tz = pytz.timezone('Asia/Yangon')
    return datetime.now(myanmar_tz)

# ==========================================
# 1. Connection Initialization
# ==========================================
@st.cache_resource
def _get_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

# Database client ကို တစ်ကြိမ်သာ ခေါ်ယူခြင်း
supabase = _get_client()

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
        "created_at": get_myanmar_time().isoformat(),
        "item": json.dumps(cart, ensure_ascii=False),
        "totals": json.dumps(totals, ensure_ascii=False),
        "status": "active" 
    }
    return supabase.table("sales").insert(data).execute()

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
    # Cache အားလုံးကိုရှင်းလင်းပြီး Stock အမှန်ရစေရန်
    st.cache_data.clear()

def process_sale_stock_update(cart):
    for item in cart:
        barcode = str(item.get("barcode"))
        product = find_by_barcode(barcode)
        if product:
            new_stock = int(product.get("stock_qty", 0)) - int(item.get("qty", 0))
            update_product_stock(barcode, new_stock)

# ==========================================
# 4. Refund Functions
# ==========================================
def execute_refund(inv, items_to_refund):
    """
    Refund လုပ်ဆောင်ချက်များကို တစ်စုတစ်စည်းတည်း လုပ်ဆောင်ပေးသည်။
    """
    if not supabase: return 0
    total_refunded = 0
    
    # 1. Stock ပြန်တိုးခြင်းနှင့် တန်ဖိုးတွက်ချက်ခြင်း
    for item in items_to_refund:
        barcode = str(item.get('barcode'))
        qty = int(item.get('qty', 0))
        
        product = find_by_barcode(barcode)
        if product:
            new_stock = int(product.get("stock_qty", 0)) + qty
            update_product_stock(barcode, new_stock)
            
        price = float(item.get('sell_price') or item.get('price') or 0)
        total_refunded += (price * qty)
    
    # 2. Refund table ထဲသို့ သိမ်းဆည်းခြင်း
    refund_data = {
        "receipt_no": inv.get('receipt_no'),
        "items": json.dumps(items_to_refund, ensure_ascii=False),
        "refund_amount": float(total_refunded),
        "refunded_at": get_myanmar_time().isoformat(),
        "details": f"Refunded {len(items_to_refund)} items"
    }
    supabase.table("refunds").insert(refund_data).execute()
    
    # 3. Sales Receipt ကို 'refunded' ဟု အမှတ်အသားပြုခြင်း
    # inv['id'] မမှန်လျှင် Error တက်နိုင်သဖြင့် ကြိုတင်စစ်ဆေးပါ
    if inv and 'id' in inv:
        supabase.table("sales").update({"status": "refunded"}).eq("id", inv['id']).execute()
    
    return total_refunded
