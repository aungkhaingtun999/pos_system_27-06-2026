# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
import re
# auth.py ၏ အပေါ်ဆုံး Import အပိုင်းကို အောက်ပါအတိုင်း ပြင်ပါ:
from database import get_all_users, update_password_db, reset_password as db_reset_password

# ==========================================
# 2. Helper Functions (Logic & Validation)
# ==========================================
def init_auth_state():
    """Initializes session state for authentication."""
    if "users" not in st.session_state:
        st.session_state.users = get_all_users()
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        
    if "username" not in st.session_state:
        st.session_state.username = None

def is_strong(password):
    """Validates if the password meets security requirements."""
    if len(password) < 8: return False
    if not re.search("[a-z]", password) or not re.search("[A-Z]", password): return False
    if not re.search("[0-9]", password) or not re.search("[!@#$%^&*]", password): return False
    return True

def logout():
    """Clears session state and resets the application state."""
    st.session_state.logged_in = False
    st.session_state.username = None
    
    keys_to_clear = ["cart", "receipt", "show_pwd_change", "receipt_totals", "receipt_no"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def perform_password_update(user, old, new, confirm):
    """Handles the business logic of updating a password."""
    current_users = get_all_users()
    
    if current_users.get(user) != old:
        return False, "❌ Password အဟောင်း မှားနေပါသည်။"
    if not is_strong(new):
        return False, "⚠️ Password သည် ၈ လုံးအထက်၊ စာလုံးအကြီး၊ အသေး၊ ဂဏန်းနှင့် သင်္ကေတများ ပါဝင်ရမည်။"
    if new != confirm:
        return False, "❌ Password အသစ် မတူပါ။"
    
    update_password_db(user, new)
    st.session_state.users[user] = new
    return True, "✅ အောင်မြင်ပါသည်။"

# ==========================================
# 3. UI Components (Run Modules)
# ==========================================
def check_password():
    """UI component for login screen."""
    init_auth_state()
    
    if not st.session_state.logged_in:
        st.subheader("🔐 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In"):
            users = get_all_users()
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else: 
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

def change_password():
    """UI component for password change form."""
    st.subheader("🔑 Password ပြောင်းလဲခြင်း")
    user = st.session_state.get("username")
    
    old = st.text_input("Old Password", type="password", key="old_pwd")
    new = st.text_input("New Password", type="password", key="new_pwd")
    confirm = st.text_input("Confirm New Password", key="conf_pwd")
    
    if st.button("Update Password"):
        success, message = perform_password_update(user, old, new, confirm)
        if success:
            st.success(message)
        else:
            st.error(message)

def reset_password(username):
    """Executes password reset and updates state."""
    if db_reset_password(username):
        init_auth_state()
        st.session_state.users[username] = "123"
        return True
    return False