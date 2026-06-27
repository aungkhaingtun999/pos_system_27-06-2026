import streamlit as st
import requests
import socket
from auth import logout, change_password
from language import get_text 

# ==========================================
# 2. Helper Functions (Connection & Navigation)
# ==========================================
def _check_internet():
    """အင်တာနက် ချိတ်ဆက်မှု ရှိမရှိ စစ်ဆေးခြင်း (မြန်ဆန်စေရန် socket သုံးထားသည်)"""
    try:
        # Google DNS ကို 2 စက္ကန့်အတွင်း စမ်းသပ်ခြင်း
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def _handle_menu_change(selected_menu):
    """Menu ပြောင်းလဲမှုကို စီမံခန့်ခွဲခြင်း"""
    st.session_state.menu = selected_menu
    st.query_params["menu"] = selected_menu
    st.rerun()

# ==========================================
# 3. Main Run Module (Sidebar UI)
# ==========================================
def show_sidebar():
    """Sidebar UI ကို Render လုပ်ပေးသော Main module"""
    with st.sidebar:
        # Internet Status Indicator (အပေါ်ဆုံးတွင်ထားခြင်းဖြင့် ချက်ချင်းသိနိုင်သည်)
        if _check_internet():
            st.success(get_text("Online", st.session_state.get("lang")))
        else:
            st.error(get_text("Offline", st.session_state.get("lang")))

        # Language Switcher
        lang_options = ["MY", "EN"]
        current_lang = st.session_state.get("lang", "MY")
        lang = st.selectbox("🌐 Language", lang_options, index=lang_options.index(current_lang))
        
        if lang != current_lang:
            st.session_state.lang = lang
            st.rerun()
            
        st.write(f"👤 User: **{st.session_state.get('username', 'Admin')}**")
        
        # Sync Data (Offline-First စနစ်အတွက် အရေးကြီးသည်)
        if st.button("🔄 Sync Data Now", key="sync_btn", use_container_width=True):
            if _check_internet():
                from sales_data import sync_to_supabase
                with st.spinner("Syncing..."):
                    sync_to_supabase()
                st.success("✅ Success")
            else:
                st.warning("⚠️ No Internet Connection")
        
        st.markdown("---")
        
        # Menu Navigation
        menu_options = ["POS System", "Inventory", "Reports", "Refund", "Profit & Loss"]
        current_menu = st.session_state.get("menu", "POS System")
        selected_menu = st.radio(
            "📌 Main Menu", 
            menu_options, 
            index=menu_options.index(current_menu) if current_menu in menu_options else 0
        )
        
        if selected_menu != current_menu:
            _handle_menu_change(selected_menu)
        
        st.markdown("---")
        
        # Password & Logout Management
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True): 
            st.session_state.show_pwd_change = True
            
        if st.session_state.get("show_pwd_change", False):
            change_password()
            if st.button("❌ Close Password", key="cls_pwd"): 
                st.session_state.show_pwd_change = False
                st.rerun()
        
        if st.button("🚪 Log Out", key="out_btn", use_container_width=True): 
            logout()

# ==========================================
# Note on Unicode (UTF-8)
# ==========================================
# ဤဖိုင်ကို သိမ်းဆည်းရာတွင် encoding="utf-8" ကို သုံးစွဲရန် မမေ့ပါနှင့်။