import streamlit as st
import re
from supabase import create_client

# Supabase Client Initialize
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ==========================================
# 1. Login Logic (Fixed)
# ==========================================
def get_user_from_db(username, password):
    """Username ကိုရှာပြီး Python ဘက်တွင် Password တိုက်စစ်ခြင်း"""
    try:
        # Username တူတာကို အရင်ရှာပါ
        response = supabase.table("users").select("*").eq("username", username).execute()
        
        # User တွေ့ရှိပါက
        if response.data:
            user = response.data[0]
            # Database password နှင့် ရိုက်ထည့်တဲ့ password တိုက်စစ်ပါ
            if str(user.get("password", "")).strip() == str(password).strip():
                return user
        return None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None

# ==========================================
# 2. Initialization & UI
# ==========================================
def init_auth_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None

def check_password():
    init_auth_state()
    if not st.session_state.logged_in:
        st.subheader("🔐 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In"):
            user_data = get_user_from_db(username, password)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.username = user_data["username"]
                st.session_state.user_role = user_data.get("role", "Cashier")
                st.rerun()
            else: 
                # Login မရလျှင် ပြရန် Error
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

# ==========================================
# 3. Security Helper (Password ပြောင်းရန်)
# ==========================================
def is_strong(password):
    return len(password) >= 8 and re.search("[A-Z]", password) and re.search("[a-z]", password) and re.search("[0-9]", password)

def update_password_db(username, old_password, new_password):
    user = get_user_from_db(username, old_password)
    if user:
        supabase.table("users").update({"password": new_password}).eq("username", username).execute()
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.rerun()
