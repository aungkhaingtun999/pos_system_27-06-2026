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
    sys.path.append(ROOT_DIR)


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
        socket.create_connection(
            ("8.8.8.8", 53),
            timeout=2
        )
        return True

    except OSError:
        return False



# ==========================================
# MENU CHANGE
# ==========================================

def _handle_menu_change(menu):

    st.session_state.menu = menu

    st.query_params["menu"] = menu

    st.rerun()



# ==========================================
# SIDEBAR
# ==========================================

def show_sidebar():

    with st.sidebar:


        # ===============================
        # CONNECTION STATUS
        # ===============================

        col1, col2 = st.columns([1,1])


        with col1:

            if _check_internet():

                st.success(
                    "🟢 Online"
                )

            else:

                st.error(
                    "🔴 Offline"
                )


        with col2:

            languages = [
                "MY",
                "EN"
            ]

            current_lang = st.session_state.get(
                "lang",
                "MY"
            )


            selected_lang = st.selectbox(

                "Language",

                languages,

                index=languages.index(
                    current_lang
                ),

                label_visibility="collapsed"

            )


            if selected_lang != current_lang:

                st.session_state.lang = selected_lang

                st.rerun()



        st.divider()



        # ===============================
        # USER INFORMATION
        # ===============================


        username = st.session_state.get(
            "username",
            "User"
        )


        role = st.session_state.get(
            "user_role",
            "Cashier"
        )


        st.info(

            f"""
👤 **{username}**

🛡️ Role : **{role}**
"""

        )



        # ===============================
        # SYNC BUTTON
        # ===============================


        if st.button(

            "🔄 Sync Data",

            use_container_width=True

        ):


            if _check_internet():


                try:

                    with st.spinner(
                        "Syncing data..."
                    ):

                        sync_to_supabase()


                    st.success(
                        "✅ Sync Complete"
                    )


                except Exception as e:

                    st.error(
                        f"Sync Error : {e}"
                    )



            else:

                st.warning(
                    "⚠️ No Internet Connection"
                )



        st.divider()



        # ===============================
        # ROLE MENU
        # ===============================


        menu_items = [

            "POS System"

        ]


        if role in [

            "Admin",

            "Inventory Manager"

        ]:

            menu_items.append(
                "Inventory"
            )


        if role == "Admin":

            menu_items.extend([

                "Reports",

                "Profit & Loss",

                "User Management"

            ])



        menu_items.append(
            "Refund"
        )



        current_menu = st.session_state.get(

            "menu",

            "POS System"

        )



        if current_menu not in menu_items:

            current_menu = "POS System"

            st.session_state.menu = current_menu



        selected_menu = st.radio(

            "📌 Main Menu",

            menu_items,

            index=menu_items.index(

                current_menu

            ),

            key="main_menu_radio"

        )



        if selected_menu != current_menu:

            _handle_menu_change(
                selected_menu
            )



        st.divider()



        # ===============================
        # PASSWORD CHANGE
        # ===============================


        if st.button(

            "🔑 Change Password",

            use_container_width=True

        ):

            st.session_state.show_pwd_change = True



        if st.session_state.get(

            "show_pwd_change",

            False

        ):


            with st.container(
                border=True
            ):

                change_password()


                if st.button(

                    "❌ Close",

                    use_container_width=True

                ):

                    st.session_state.show_pwd_change = False

                    st.rerun()



        # ===============================
        # LOGOUT
        # ===============================


        if st.button(

            "🚪 Logout",

            use_container_width=True

        ):

            logout()
