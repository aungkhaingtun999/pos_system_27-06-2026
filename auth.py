import streamlit as st
import re
import sys
import os

# --- Path Configuration (Database ကိုသေချာရှာနိုင်ရန်) ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database Import (Error မတက်စေရန် Try-Except သုံးထားသည်)
try:
    from database import get_user_from_db, update_password_db, reset_password as db_reset_password
except ImportError:
    try:
        from components.database import get_user_from_db, update_password_db, reset_password as db_reset_password
    except ImportError:
        st.error("❌ Database module ကို ရှာမတွေ့ပါ။ ဖိုင်တည်နေရာကို စစ်ဆေးပါ။")

# ==========================================
# 1. Initialization
# ==========================================
def init_auth_state():
    """Session state များကို Initialize လုပ်ခြင်း"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None

# ==========================================
# 2. Helper Functions
# ==========================================
def is_strong(password):
    """Password လုံခြုံရေး စစ်ဆေးခြင်း"""
    if len(password) < 8: return False
    if not re.search("[a-z]", password) or not re.search("[A-Z]", password): return False
    if not re.search("[0-9]", password) or not re.search("[!@#$%^&*]", password): return False
    return True

def logout():
    """Logout လုပ်ပြီး Session ရှင်းလင်းခြင်း"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    
    # ဆက်စပ်နေသော Session keys များရှင်းလင်းခြင်း
    keys_to_clear = ["cart", "receipt", "show_pwd_change", "receipt_totals", "receipt_no", "menu"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 3. Main Auth Logic
# ==========================================
def check_password():
    """Login UI လုပ်ဆောင်ချက်"""
    init_auth_state()
    
    if not st.session_state.logged_in:
        st.subheader("🔐 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In"):
            # Database မှ User data (role ပါ) ကို ဆွဲထုတ်ခြင်း
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

def perform_password_update(username, old, new, confirm):
    """Password အဟောင်း/အသစ် စစ်ဆေးပြီး Database ထဲသို့ Update လုပ်ခြင်း"""
    if not is_strong(new):
        return False, "⚠️ Password သည် ၈ လုံးအထက်၊ စာလုံးအကြီး၊ အသေး၊ ဂဏန်းနှင့် သင်္ကေတများ ပါဝင်ရမည်။"
    if new != confirm:
        return False, "❌ Password အသစ် မတူပါ။"
    
    if update_password_db(username, old, new):
        return True, "✅ Password အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။"
    else:
        return False, "❌ Password အဟောင်း မှားနေပါသည်။"

def change_password():
    """Password ပြောင်းလဲခြင်း UI"""
    st.subheader("🔑 Password ပြောင်းလဲခြင်း")
    user = st.session_state.get("username")
    
    old = st.text_input("Old Password", type="password", key="old_pwd")
    new = st.text_input("New Password", type="password", key="new_pwd")
    confirm = st.text_input("Confirm New Password", type="password", key="conf_pwd")
    
    if st.button("Update Password"):
        success, message = perform_password_update(user, old, new, confirm)
        if success:
            st.success(message)
        else:
            st.error(message)

def reset_password(username):
    """Admin အနေဖြင့် User တစ်ဦး၏ Password ကို Reset လုပ်ခြင်း"""
    if st.session_state.user_role == "Admin":
        return db_reset_password(username)
    return False
