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

supabase = _get_client()

# ==========================================
# 2. Sale & Stock Functions
# ==========================================
def insert_sale(cart, totals, receipt_no, payment_method, customer_name):
    """Database သို့ Sales အသစ်ထည့်ခြင်း"""
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

def process_sale_stock_update(cart):
    """Sale လုပ်သည့်အခါ Stock ကို အလိုအလျောက် နုတ်ပေးခြင်း"""
    if not supabase: return
    for item in cart:
        barcode = str(item.get("barcode"))
        qty = int(item.get("qty", 0))
        
        product = supabase.table("products").select("stock_qty").eq("barcode", barcode).single().execute().data
        if product:
            new_stock = int(product.get("stock_qty", 0)) - qty
            supabase.table("products").update({"stock_qty": new_stock}).eq("barcode", barcode).execute()

def sync_to_supabase(pending_sales):
    """
    Offline မှရရှိသော Pending Sales များအားလုံးကို Cloud သို့ တင်ပေးခြင်း
    pending_sales သည် List တစ်ခုဖြစ်သည်
    """
    if not supabase: raise Exception("Database Connection မရှိပါ။")
    
    # ဤနေရာတွင် loop ပတ်ပြီး တစ်ခုချင်းစီကို database (sales table) ထဲ ထည့်ခြင်း
    for sale in pending_sales:
        try:
            # sale ဆိုသည်မှာ dict တစ်ခုဖြစ်သည်
            # insert_sale function ကို ခေါ်သုံးပါ
            insert_sale(
                sale['cart'], 
                sale['totals'], 
                sale['rec_no'], 
                sale['payment_method'], 
                sale['customer']
            )
        except Exception as e:
            print(f"Sync error for receipt {sale.get('rec_no')}: {e}")
            continue # တစ်ခု error တက်ရင် နောက်တစ်ခု ဆက်လုပ်မည်

# ==========================================
# 3. Optimized Refund Function
# ==========================================
def execute_refund(inv, items_to_refund):
    """
    Refund လုပ်ဆောင်ချက် - Atomic Locking ဖြင့် တည်ဆောက်ထားသည်
    """
    if not supabase: return 0
    
    # [Step 1]: Database မှ လက်ရှိ status ကို နောက်ဆုံးတစ်ကြိမ် တိုက်ရိုက်စစ်ပါ
    latest_check = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
    if latest_check and latest_check.get("status") == "refunded":
        raise Exception("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")

    # [Step 2 - CRITICAL]: Refund မစခင် status ကို 'refunded' အရင်ပြောင်းထားပါ (Locking)
    supabase.table("sales").update({"status": "refunded"}).eq("id", inv['id']).execute()

    try:
        total_refunded = 0
        # [Step 3]: Stock ပြန်တိုးခြင်း
        for item in items_to_refund:
            barcode = str(item.get('barcode'))
            qty = int(item.get('qty', 0))
            
            product = supabase.table("products").select("stock_qty").eq("barcode", barcode).single().execute().data
            if product:
                new_stock = int(product.get("stock_qty", 0)) + qty
                supabase.table("products").update({"stock_qty": new_stock}).eq("barcode", barcode).execute()
                
            price = float(item.get('sell_price') or item.get('price') or 0)
            total_refunded += (price * qty)
        
        # [Step 4]: Refund Log သိမ်းခြင်း
        refund_data = {
            "receipt_no": inv.get('receipt_no'),
            "items": json.dumps(items_to_refund, ensure_ascii=False),
            "refund_amount": float(total_refunded),
            "refunded_at": get_myanmar_time().isoformat(),
            "details": f"Refunded {len(items_to_refund)} items"
        }
        supabase.table("refunds").insert(refund_data).execute()
        
        return total_refunded

    except Exception as e:
        raise Exception(f"Refund လုပ်ဆောင်စဉ် အမှားဖြစ်ပွားသည်: {e}")
