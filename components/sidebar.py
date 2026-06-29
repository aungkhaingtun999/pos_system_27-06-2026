import streamlit as st
import socket
import sys
import os

# ==========================================
# PATH SETUP
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# ==========================================
# IMPORTS
# ==========================================
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
# SIDEBAR
# ==========================================
def show_sidebar():

    # INIT STATE SAFELY
    if "lang" not in st.session_state:
        st.session_state.lang = "MY"

    if "menu" not in st.session_state:
        st.session_state.menu = "POS System"


    with st.sidebar:

        # -------------------------
        # STATUS
        # -------------------------
        col1, col2 = st.columns(2)

        with col1:
            if _check_internet():
                st.success("🟢 Online")
            else:
                st.error("🔴 Offline")

        with col2:
            lang = st.selectbox(
                "🌐",
                ["MY", "EN"],
                index=["MY", "EN"].index(st.session_state.lang),
                label_visibility="collapsed"
            )

            if lang != st.session_state.lang:
                st.session_state.lang = lang
                st.rerun()


        st.divider()


        # -------------------------
        # SYNC BUTTON
        # -------------------------
        if st.button("🔄 Sync Data Now", use_container_width=True):

            if _check_internet():

                try:
                    from components.supabase_logic import sync_to_supabase

                    with st.spinner("Syncing..."):

                        pending = st.session_state.get("pending_sales", [])

                        # SAFE CALL
                        if pending:
                            sync_to_supabase(pending)

                            st.session_state.pending_sales = []

                    st.success("✅ Sync Complete")

                except Exception as e:
                    st.error(f"❌ Sync Failed: {e}")

            else:
                st.warning("⚠️ No Internet Connection")


        st.divider()


        # -------------------------
        # ROLE MENU
        # -------------------------
        role = st.session_state.get("user_role", "Cashier")

        menu_items = [
            "POS System",
            "Refund"
        ]

        if role in ["Admin", "Inventory Manager"]:
            menu_items.insert(1, "Inventory")

        if role == "Admin":
            menu_items.extend([
                "Reports",
                "Profit & Loss",
                "User Management"
            ])


        # 🔥 IMPORTANT FIX: normalize current menu
        current_menu = st.session_state.get("menu", "POS System")

        if current_menu not in menu_items:
            current_menu = "POS System"
            st.session_state.menu = current_menu   # FIX: state sync


        selected_menu = st.radio(
            "📌 Main Menu",
            menu_items,
            index=menu_items.index(current_menu),
            key="main_menu_radio"
        )


        if selected_menu != current_menu:
            st.session_state.menu = selected_menu

            try:
                st.query_params["menu"] = selected_menu
            except:
                pass

            st.rerun()


        st.divider()


        # -------------------------
        # PASSWORD
        # -------------------------
        if st.button("🔑 Change Password", use_container_width=True):
            st.session_state.show_pwd_change = True


        if st.session_state.get("show_pwd_change"):

            with st.container(border=True):

                change_password()

                if st.button("❌ Close", use_container_width=True):
                    st.session_state.show_pwd_change = False
                    st.rerun()


        # -------------------------
        # LOGOUT
        # -------------------------
        if st.button("🚪 Log Out", use_container_width=True):
            logout()
