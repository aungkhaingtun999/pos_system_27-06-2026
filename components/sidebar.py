import streamlit as st
import socket
import sys
import os

# Root folder ကို ရှာဖွေပြီး path ထဲကို ထည့်ခြင်း
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Imports - ဤနေရာတွင် 'components.' ကို ဖြုတ်လိုက်ပါ
from auth import logout, change_password
from language import get_text
from components.supabase_logic import sync_to_supabase
# --- Imports ---
from auth import logout, change_password
from language import get_text
# အရေးကြီး: sys.path ထဲတွင် root_dir ရှိနေပြီဖြစ်သောကြောင့် 
# 'components.supabase_logic' ဟု ခေါ်နိုင်ပါပြီ
from components.supabase_logic import sync_to_supabase

# ==========================================
# IMPORTS
# ==========================================
from auth import logout, change_password
from language import get_text
from components.supabase_logic import sync_to_supabase

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
# MENU CHANGE
# ==========================================
def _handle_menu_change(selected_menu):
    st.session_state.menu = selected_menu
    try:
        st.query_params["menu"] = selected_menu
    except Exception:
        pass
    st.rerun()

# ==========================================
# SIDEBAR UI
# ==========================================
def show_sidebar():
    # Session Defaults
    if "lang" not in st.session_state:
        st.session_state.lang = "MY"
    if "menu" not in st.session_state:
        st.session_state.menu = "POS System"

    with st.sidebar:
        # --- STATUS AREA ---
        col1, col2 = st.columns([1, 1])
        with col1:
            if _check_internet():
                st.success("🟢 Online")
            else:
                st.error("🔴 Offline")
        with col2:
            lang_options = ["MY", "EN"]
            current_lang = st.session_state.lang
            selected_lang = st.selectbox("🌐", lang_options, index=lang_options.index(current_lang), label_visibility="collapsed")
            if selected_lang != current_lang:
                st.session_state.lang = selected_lang
                st.rerun()

        st.divider()

        # --- USER INFO ---
        username = st.session_state.get("username", "User")
        role = st.session_state.get("user_role", "Cashier")
        st.info(f"👤 **{username}**\n\n🛡️ Role : **{role}**")

        # --- SYNC DATA ---
        if st.button("🔄 Sync Data Now", key="sync_btn", use_container_width=True):
            if _check_internet():
                try:
                    with st.spinner("Syncing..."):
                        sync_to_supabase()
                    st.success("✅ Sync Complete")
                except Exception as e:
                    st.error(f"❌ Sync Failed\n\n{e}")
            else:
                st.warning("⚠️ No Internet Connection")

        st.divider()

        # --- ROLE MENU ---
        menu_items = ["POS System"]
        if role in ["Admin", "Inventory Manager"]:
            menu_items.append("Inventory")
        if role == "Admin":
            menu_items.extend(["Reports", "Profit & Loss", "User Management"])
        menu_items.append("Refund")

        current_menu = st.session_state.menu
        if current_menu not in menu_items:
            current_menu = "POS System"
            st.session_state.menu = current_menu

        selected_menu = st.radio(
            "📌 Main Menu",
            menu_items,
            index=menu_items.index(current_menu),
            key="main_menu_radio"
        )

        if selected_menu != current_menu:
            _handle_menu_change(selected_menu)

        st.divider()

        # --- PASSWORD CHANGE ---
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True):
            st.session_state.show_pwd_change = True

        if st.session_state.get("show_pwd_change", False):
            with st.container(border=True):
                change_password()
                if st.button("❌ Close", key="cls_pwd", use_container_width=True):
                    st.session_state.show_pwd_change = False
                    st.rerun()

        # --- LOGOUT ---
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            logout()
