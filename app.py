import sys
import os
import streamlit as st


# ==========================================
# PATH SETUP
# ==========================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)



# ==========================================
# IMPORTS
# ==========================================

from auth import check_password, init_auth_state
from utils import init_app_state
from config import init_session


from components.supabase_logic import sync_to_supabase

from components.sidebar import show_sidebar

from components.pos_system import show_pos_system
from components.reports import show_reports
from components.inventory import show_inventory
from components.profit_loss import show_profit_loss
from components.refund import show_refund
from components.receipt import show_receipt
from components.user_management import show_user_management




# ==========================================
# PAGE CONFIG
# ==========================================

def setup_page():

    if "page_config_done" not in st.session_state:

        st.set_page_config(
            page_title="Barcode POS System",
            layout="wide"
        )

        st.session_state.page_config_done = True





# ==========================================
# AUTO SYNC
# ==========================================

def auto_sync_on_start():

    pending_data = st.session_state.get(
        "pending_sales",
        []
    )


    if not pending_data:
        return


    if not isinstance(
        pending_data,
        list
    ):

        st.session_state.pending_sales = []
        return



    try:

        sync_to_supabase(
            pending_data
        )

        st.session_state.pending_sales = []


        st.success(
            "✅ Cloud Sync အောင်မြင်ပါသည်"
        )


    except Exception as e:


        st.warning(
            f"⚠️ Sync မအောင်မြင်ပါ : {e}"
        )





# ==========================================
# MAIN APP
# ==========================================

def main():


    setup_page()


    # Session Initialize

    init_auth_state()

    init_app_state()

    init_session()



    # ======================================
    # LOGIN
    # ======================================

    if not check_password():

        st.stop()



    # ======================================
    # SIDEBAR
    # ======================================

    show_sidebar()



    # ======================================
    # MENU ROUTER
    # ======================================

    menu_map = {

        "POS System": show_pos_system,

        "Inventory": show_inventory,

        "Reports": show_reports,

        "Profit & Loss": show_profit_loss,

        "Refund": show_refund,

        "User Management": show_user_management,

    }



    current_menu = st.session_state.get(
        "menu",
        "POS System"
    )



    # Unknown menu protection

    if current_menu not in menu_map:


        st.warning(
            f"Unknown Menu : {current_menu}"
        )


        current_menu = "POS System"



    # Run Selected Page

    menu_map[current_menu]()





    # ======================================
    # AUTO SYNC
    # ======================================

    auto_sync_on_start()





    # ======================================
    # RECEIPT DISPLAY
    # ======================================

    if st.session_state.get(
        "receipt"
    ):


        show_receipt(

            data=st.session_state.receipt,

            totals=st.session_state.receipt_totals,

            receipt_no=st.session_state.get(
                "receipt_no",
                "N/A"
            ),


            payment_method=st.session_state.get(
                "current_payment_method",
                "Cash"
            ),


            customer=st.session_state.get(
                "current_customer",
                "Walk-in"
            )

        )



        if st.button(
            "🧾 Close Receipt"
        ):


            st.session_state.receipt = None

            st.session_state.receipt_totals = None

            st.rerun()





# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    main()
