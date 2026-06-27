# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
import pandas as pd
from supabase import create_client
from config import SUPABASE_CONFIG

# ==========================================
# 2. Helper Functions (Connection & Config)
# ==========================================
@st.cache_resource
def _get_client():
    """Supabase client ကို Initialize လုပ်ခြင်း"""
    if not SUPABASE_CONFIG["url"] or not SUPABASE_CONFIG["key"]:
        st.error("Supabase credentials not found!")
        return None
    return create_client(SUPABASE_CONFIG["url"], SUPABASE_CONFIG["key"])

supabase = _get_client()

# ==========================================
# 3. Main Run Modules (Product Operations)
# ==========================================

# --- Fetching & Caching ---
def get_inventory():
    """Database မှ Data အားလုံးကို DataFrame အဖြစ် ရယူခြင်း"""
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table("products").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching inventory: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_products_cached():
    """Performance အတွက် Cache မှတဆင့် Products ရယူခြင်း"""
    df = get_inventory()
    return df.to_dict('records') if not df.empty else []

# --- Search & Find ---
def find_by_barcode(barcode):
    """Barcode ဖြင့် ရှာဖွေခြင်း"""
    products = get_products_cached()
    return next((p for p in products if str(p.get("barcode")) == str(barcode)), None)

def search_by_name(keyword):
    """နာမည်ဖြင့် ရှာဖွေခြင်း"""
    if not keyword: return []
    products = get_products_cached()
    return [p for p in products if keyword.lower() in str(p.get("product_name", "")).lower()]

# --- CRUD Operations ---
def add_new_product(product_data):
    try:
        response = supabase.table("products").insert(product_data).execute()
        st.cache_data.clear()
        return response
    except Exception as e:
        st.error(f"Error adding product: {e}")
        return None

def update_product_stock(barcode, new_stock):
    try:
        response = supabase.table("products").update({"stock_qty": int(new_stock)}).eq("barcode", barcode).execute()
        st.cache_data.clear()
        return response
    except Exception as e:
        st.error(f"Error updating stock: {e}")
        return None

def update_product_price(barcode, new_buy_price, new_sell_price):
    try:
        response = supabase.table("products").update({
            "buy_price": float(new_buy_price), 
            "sell_price": float(new_sell_price)
        }).eq("barcode", barcode).execute()
        st.cache_data.clear()
        return response
    except Exception as e:
        st.error(f"Error updating price: {e}")
        return None

def delete_product(barcode):
    try:
        response = supabase.table("products").delete().eq("barcode", barcode).execute()
        st.cache_data.clear()
        return response
    except Exception as e:
        st.error(f"Error deleting product: {e}")
        return None

# --- Business Logic ---
def process_sale_stock_update(cart):
    """အရောင်းဖြစ်တိုင်း Stock အလိုအလျောက် နုတ်ပေးခြင်း"""
    for item in cart:
        barcode = str(item.get("barcode"))
        product = find_by_barcode(barcode)
        if product:
            new_stock = int(product.get("stock_qty", 0)) - int(item.get("qty", 0))
            update_product_stock(barcode, new_stock)
    st.cache_data.clear()

def calculate_profit(cart):
    """စုစုပေါင်းအမြတ် တွက်ချက်ခြင်း"""
    return sum((float(item.get("sell_price", 0)) - float(item.get("buy_price", 0))) * int(item.get("qty", 0)) for item in cart)

def get_low_stock_products(threshold=5):
    """Stock နည်းသော ပစ္စည်းများ စစ်ထုတ်ခြင်း"""
    return [p for p in get_products_cached() if int(p.get("stock_qty", 0)) <= threshold]