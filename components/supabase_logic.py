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

# supabase ကို module-level မှာတင် Define လုပ်ပါ
supabase = _get_client()

def _clear_cache():
    st.cache_data.clear()

# ==========================================
# 2. Database Functions
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

def sync_to_supabase():
    """Pending sales များကို Cloud သို့ Sync လုပ်ပေးသော Function"""
    if "pending_sales" not in st.session_state or not st.session_state.pending_sales:
        return
    
    for sale in list(st.session_state.pending_sales):
        try:
            insert_sale_to_supabase(
                sale['cart'], sale['totals'], sale['rec_no'], 
                sale['payment_method'], sale['customer']
            )
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
    except Exception as e:
        return []

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
