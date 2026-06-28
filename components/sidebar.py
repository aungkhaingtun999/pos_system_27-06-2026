import streamlit as st
import socket
import sys
import os

# PATH SETUP: Root folder ကို path ထဲသို့ အတင်းထည့်ခြင်း
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from auth import logout, change_password
from language import get_text

# ==========================================
# INTERNET CHECK
# ==========================================
def _check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

# ==========================================
# SIDEBAR UI
# ==========================================
def show_sidebar():
    if "lang" not in st.session_state: st.session_state.lang = "MY"
    if "menu" not in st.session_state: st.session_state.menu = "POS System"

    with st.sidebar:
        # Status Area
        col1, col2 = st.columns([1, 1])
        with col1:
            st.success("🟢 Online") if _check_internet() else st.error("🔴 Offline")
        with col2:
            lang_options = ["MY", "EN"]
            selected_lang = st.selectbox("🌐", lang_options, index=lang_options.index(st.session_state.lang), label_visibility="collapsed")
            if selected_lang != st.session_state.lang:
                st.session_state.lang = selected_lang
                st.rerun()

        st.divider()

        # Sync Data (ဒီနေရာမှာ Local Import လုပ်ခြင်းဖြင့် အမှားကင်းစေသည်)
        if st.button("🔄 Sync Data Now", key="sync_btn", use_container_width=True):
            if _check_internet():
                try:
                    from components.supabase_logic import sync_to_supabase
                    with st.spinner("Syncing..."):
                        sync_to_supabase()
                    st.success("✅ Sync Complete")
                except Exception as e:
                    st.error(f"❌ Sync Failed: {e}")
            else:
                st.warning("⚠️ No Internet Connection")

        st.divider()

        # Role Menu
        role = st.session_state.get("user_role", "Cashier")
        menu_items = ["POS System"]
        if role in ["Admin", "Inventory Manager"]: menu_items.append("Inventory")
        if role == "Admin": menu_items.extend(["Reports", "Profit & Loss", "User Management"])
        menu_items.append("Refund")

        current_menu = st.session_state.menu
        if current_menu not in menu_items: current_menu = "POS System"

        selected_menu = st.radio("📌 Main Menu", menu_items, index=menu_items.index(current_menu), key="main_menu_radio")
        if selected_menu != current_menu:
            st.session_state.menu = selected_menu
            try: st.query_params["menu"] = selected_menu
            except: pass
            st.rerun()

        st.divider()

        # Password & Logout
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True):
            st.session_state.show_pwd_change = True

        if st.session_state.get("show_pwd_change", False):
            with st.container(border=True):
                change_password()
                if st.button("❌ Close", key="cls_pwd", use_container_width=True):
                    st.session_state.show_pwd_change = False
                    st.rerun()

        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            logout()
