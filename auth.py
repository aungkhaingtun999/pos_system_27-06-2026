import streamlit as st
import re
from supabase import create_client

# Supabase Client Initialize လုပ်ခြင်း
# သေချာစေရန် Secrets မှ URL နှင့် Key ကို ခေါ်ယူပါ
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ==========================================
# 1. Initialization
# ==========================================
def init_auth_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None

# ==========================================
# 2. Database Helpers (Supabase Queries)
# ==========================================
def get_user_from_db(username, password):
    """Username ကိုသာရှာပြီး Python ဘက်တွင် Password ကို တိုက်စစ်ခြင်း"""
    try:
        # Username ကိုသာ Query လုပ်ပါ
        response = supabase.table("users").select("*").eq("username", username).execute()
        
        if response.data:
            user = response.data[0]
            # Database ထဲက password နှင့် တိုက်စစ်ပါ (Space များကို strip လုပ်ပေးပါ)
            if str(user.get("password", "")).strip() == str(password).strip():
                return user
        return None
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

def update_password_db(username, old_password, new_password):
    """Password အဟောင်းမှန်မမှန်စစ်၍ အသစ်ပြောင်းခြင်း"""
    user = get_user_from_db(username, old_password)
    if user:
        try:
            supabase.table("users").update({"password": new_password}).eq("username", username).execute()
            return True
        except:
            return False
    return False

def reset_password(username):
    """Admin အနေဖြင့် Password ကို 123 သို့ ပြန်လည် Reset လုပ်ခြင်း"""
    try:
        supabase.table("users").update({"password": "123"}).eq("username", username).execute()
        return True
    except:
        return False

# ==========================================
# 3. Security & Logic
# ==========================================
def is_strong(password):
    if len(password) < 8: return False
    if not re.search("[a-z]", password) or not re.search("[A-Z]", password): return False
    if not re.search("[0-9]", password) or not re.search("[!@#$%^&*]", password): return False
    return True

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    keys_to_clear = ["cart", "receipt", "show_pwd_change", "receipt_totals", "receipt_no", "menu"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 4. Main Auth UI
# ==========================================
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
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

def change_password():
    st.subheader("🔑 Password ပြောင်းလဲခြင်း")
    user = st.session_state.get("username")
    old = st.text_input("Old Password", type="password", key="old_pwd")
    new = st.text_input("New Password", type="password", key="new_pwd")
    confirm = st.text_input("Confirm New Password", type="password", key="conf_pwd")
    
    if st.button("Update Password"):
        if not is_strong(new):
            st.error("⚠️ Password သည် ၈ လုံးအထက်၊ စာလုံးအကြီး၊ အသေး၊ ဂဏန်းနှင့် သင်္ကေတများ ပါဝင်ရမည်။")
        elif new != confirm:
            st.error("❌ Password အသစ် မတူပါ။")
        elif update_password_db(user, old, new):
            st.success("✅ Password အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။")
        else:
            st.error("❌ Password အဟောင်း မှားနေပါသည်။")
