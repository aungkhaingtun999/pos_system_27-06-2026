# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
from config import SUPABASE_CONFIG
from supabase import create_client
import json

# ==========================================
# 2. Supabase Client Initialize
# ==========================================
try:
    supabase = create_client(SUPABASE_CONFIG["url"], SUPABASE_CONFIG["key"])
except Exception as e:
    st.error(f"Supabase Client Error: {e}")
    supabase = None

# ==========================================
# 3. Database Operations (Users & Auth)
# ==========================================

def get_all_users():
    """Supabase မှ User စာရင်းအားလုံးကို ရယူခြင်း"""
    if not supabase: return {}
    try:
        response = supabase.table("users").select("username, password").execute()
        return {item["username"]: item["password"] for item in response.data}
    except Exception as e:
        print(f"Error fetching users: {e}")
        return {}

def update_password_db(username, new_password):
    """Supabase တွင် Password အသစ် update လုပ်ခြင်း"""
    if not supabase: return False
    try:
        supabase.table("users").update({"password": new_password}).eq("username", username).execute()
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False

def reset_password(username):
    """Password အား '123456' သို့ ပြန်လည်သတ်မှတ်ခြင်း"""
    if not supabase: return False
    try:
        supabase.table("users").update({"password": "123456"}).eq("username", username).execute()
        return True
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False

# ==========================================
# 4. Sync Operations (Offline-First Logic)
# ==========================================

def sync_to_supabase():
    """Local Session မှ Pending Data များကို Supabase သို့ Sync လုပ်ခြင်း"""
    if not supabase: return
    
    # Session state ထဲမှာ Pending Data ရှိမရှိ စစ်ဆေးခြင်း
    if "pending_sales" in st.session_state and st.session_state.pending_sales:
        success_count = 0
        for sale in list(st.session_state.pending_sales):
            try:
                # အရောင်းမှတ်တမ်းတစ်ခုချင်းစီကို Cloud သို့ ပို့ခြင်း
                data = {
                    "receipt_no": sale['rec_no'],
                    "customer_name": sale['customer'],
                    "grand_total": float(sale['totals'].get("grand_total", 0)),
                    "payment_type": sale['payment_method'],
                    "item": json.dumps(sale['cart'], ensure_ascii=False),
                    "totals": json.dumps(sale['totals'], ensure_ascii=False)
                }
                supabase.table("sales").insert(data).execute()
                
                # အောင်မြင်ပါက Pending list မှ ဖယ်ထုတ်ခြင်း
                st.session_state.pending_sales.remove(sale)
                success_count += 1
            except Exception as e:
                print(f"Sync Error for {sale['rec_no']}: {e}")
                break # တစ်ခုခု error တက်ရင် ရပ်ထားမည်
        
        if success_count > 0:
            st.success(f"✅ အရောင်း {success_count} ခု Sync အောင်မြင်ပါသည်။")

def insert_single_sale(sale_data):
    """တစ်ခါတည်း အရောင်းတစ်ခုကို Cloud သို့ ပို့ခြင်း"""
    if not supabase: return False
    try:
        supabase.table("sales").insert(sale_data).execute()
        return True
    except Exception as e:
        print(f"Error syncing to Supabase: {e}")
        return False

# ==========================================
# 5. Product & Inventory Logic
# ==========================================
def get_remote_products():
    """Supabase မှ ပစ္စည်းစာရင်းများကို ရယူခြင်း"""
    if not supabase: return []
    try:
        return supabase.table("products").select("*").execute().data
    except Exception as e:
        print(f"Error fetching remote products: {e}")
        return []

def update_remote_stock(barcode, new_stock):
    """Cloud တွင် Stock ပမာဏ update လုပ်ခြင်း"""
    if not supabase: return False
    try:
        supabase.table("products").update({"stock_qty": int(new_stock)}).eq("barcode", barcode).execute()
        return True
    except Exception as e:
        print(f"Error updating remote stock: {e}")
        return False