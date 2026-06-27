import streamlit as st
import requests
import socket
from auth import logout, change_password
from language import get_text 

# ==========================================
# 2. Helper Functions (Connection & Navigation)
# ==========================================
def _check_internet():
    """အင်တာနက် ချိတ်ဆက်မှု ရှိမရှိ စစ်ဆေးခြင်း"""
    try:
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
    """Sidebar UI - Role-based access ပါဝင်သည်။"""
    with st.sidebar:
        # 1. Internet Status
        if _check_internet():
            st.success(get_text("Online", st.session_state.get("lang")))
        else:
            st.error(get_text("Offline", st.session_state.get("lang")))

        # 2. Language Switcher
        lang_options = ["MY", "EN"]
        current_lang = st.session_state.get("lang", "MY")
        lang = st.selectbox("🌐 Language", lang_options, index=lang_options.index(current_lang))
        if lang != current_lang:
            st.session_state.lang = lang
            st.rerun()
            
        # 3. User Info
        # အရေးကြီးချက်: role ကို session ကမရရင် 'Cashier' လို့ သတ်မှတ်ပေးထားသည်
        role = st.session_state.get("user_role", "Cashier") 
        username = st.session_state.get('username', 'User')
        st.write(f"👤 User: **{username}**")
        st.caption(f"🛡️ Role: {role}")
        
        # 4. Sync Data
        if st.button("🔄 Sync Data Now", key="sync_btn", use_container_width=True):
            if _check_internet():
                from sales_data import sync_to_supabase
                with st.spinner("Syncing..."):
                    sync_to_supabase()
                st.success("✅ Success")
            else:
                st.warning("⚠️ No Internet Connection")
        
        st.markdown("---")
        
        # 5. Role-Based Menu Navigation
        # အကောင့်အမျိုးအစားအလိုက် Menu စစ်ဆေးခြင်း
        menu_items = ["POS System"]
        
        # Role ပေါ်မူတည်ပြီး Menu များ ထပ်ဖြည့်ခြင်း
        if role in ["Admin", "Inventory Manager"]:
            menu_items.append("Inventory")
            
        if role == "Admin":
            menu_items.extend(["Reports", "Profit & Loss", "User Management"])
            
        menu_items.append("Refund")

        # လက်ရှိ menu က menu_items ထဲမှာ ရှိမရှိ စစ်ဆေးပြီးမှ index ရှာပါ
        current_menu = st.session_state.get("menu", "POS System")
        if current_menu not in menu_items:
            current_menu = "POS System"
            
        selected_menu = st.radio(
            "📌 Main Menu", 
            menu_items, 
            index=menu_items.index(current_menu)
        )
        
        if selected_menu != current_menu:
            _handle_menu_change(selected_menu)
        
        st.markdown("---")
        
        # 6. Password & Logout Management
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True): 
            st.session_state.show_pwd_change = True
            
        if st.session_state.get("show_pwd_change", False):
            change_password()
            if st.button("❌ Close Password", key="cls_pwd"): 
                st.session_state.show_pwd_change = False
                st.rerun()
        
        if st.button("🚪 Log Out", key="out_btn", use_container_width=True): 
            logout()
