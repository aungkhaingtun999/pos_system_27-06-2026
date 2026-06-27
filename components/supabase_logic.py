import streamlit as st
import json
from supabase import create_client
from datetime import datetime

# ==========================================
# 1. Connection Initialization
# ==========================================
@st.cache_resource
def _get_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase = _get_client()

def _clear_cache():
    st.cache_data.clear()

# ==========================================
# 2. Product & Stock Management
# ==========================================
@st.cache_data(ttl=600)
def get_products_cached():
    if not supabase: return []
    try:
        response = supabase.table("products").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return []

def find_by_barcode(barcode):
    products = get_products_cached()
    return next((p for p in products if str(p.get("barcode")) == str(barcode)), None)

def update_product_stock(barcode, new_stock):
    try:
        # Stock အသစ်ကို update လုပ်ခြင်း
        supabase.table("products").update({"stock_qty": int(new_stock)}).eq("barcode", barcode).execute()
        _clear_cache()
    except Exception as e:
        st.error(f"Stock Update Error: {e}")
        raise e

def process_sale_stock_update(cart):
    """Sale ပြီးတိုင်း Stock အလိုအလျောက်လျှော့ရန်"""
    for item in cart:
        barcode = str(item.get("barcode"))
        product = find_by_barcode(barcode)
        if product:
            new_stock = int(product.get("stock_qty", 0)) - int(item.get("qty", 0))
            update_product_stock(barcode, new_stock)

def reverse_stock_update(barcode, qty_to_add):
    """Refund လုပ်သည့်အခါ Stock ပြန်တိုးရန်"""
    product = find_by_barcode(barcode)
    if product:
        new_stock = int(product.get("stock_qty", 0)) + int(qty_to_add)
        update_product_stock(barcode, new_stock)

# ==========================================
# 3. Sales & Refund Records
# ==========================================
def insert_sale_to_supabase(cart, totals, receipt_no, payment_method, customer_name):
    if not supabase:
        raise Exception("Database Connection မရှိပါ။")
    
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

def execute_refund(inv, items_to_refund):
    total_refunded = 0
    try:
        for item in items_to_refund:
            barcode = str(item.get('barcode'))
            qty = int(item.get('qty', 0))
            reverse_stock_update(barcode, qty)
            
            price = float(item.get('sell_price') or item.get('price') or 0)
            total_refunded += (price * qty)
        
        refund_data = {
            "receipt_no": inv.get('receipt_no'),
            "items": json.dumps(items_to_refund, ensure_ascii=False),
            "refund_amount": float(total_refunded),
            "refunded_at": datetime.now().isoformat()
        }
        supabase.table("refunds").insert(refund_data).execute()
        
        # Log ရေးမှတ်ခြင်း
        log_refund(inv.get('receipt_no'), items_to_refund, total_refunded)
        return total_refunded
    except Exception as e:
        st.error(f"Refund Process Error: {e}")
        return 0

def log_refund(receipt_no, items, total_refunded):
    """Refund Log ကို Database တွင် တိုက်ရိုက်မှတ်တမ်းတင်ခြင်း"""
    try:
        log_data = {
            "receipt_no": receipt_no,
            "details": f"Refunded {len(items)} items",
            "amount": float(total_refunded),
            "timestamp": datetime.now().isoformat()
        }
        supabase.table("refund_logs").insert(log_data).execute()
    except Exception as e:
        print(f"Logging Error: {e}")
