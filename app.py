import sys
import os
import streamlit as st

# ==========================================
# PATH SETUP
# ==========================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
# PAGE CONFIG (IMPORTANT FIX)
# ==========================================
def setup_page():
    st.set_page_config(
        page_title="Barcode POS System",
        layout="wide"
    )


# ==========================================
# AUTO SYNC (SAFE VERSION)
# ==========================================
def auto_sync_on_start():

    pending_data = st.session_state.get("pending_sales")

    if not pending_data:
        return

    if not isinstance(pending_data, list):
        st.session_state.pending_sales = []
        return

    try:
        sync_to_supabase(pending_data)
        st.session_state.pending_sales = []
        st.success("✅ Cloud Sync အောင်မြင်ပါသည်")
    except Exception as e:
        st.warning(f"⚠️ Sync မအောင်မြင်ပါ: {e}")


# ==========================================
# MAIN APP
# ==========================================
def main():

    setup_page()

    init_auth_state()
    init_app_state()
    init_session()

    # --------------------------
    # LOGIN CHECK
    # --------------------------
    if not check_password():
        st.stop()

    # --------------------------
    # SIDEBAR
    # --------------------------
    show_sidebar()

    # --------------------------
    # MENU ROUTER (FIXED)
    # --------------------------
    menu_map = {
    "POS System": show_pos_system,
    "Inventory": show_inventory,
    "Reports": show_reports,
    "Profit & Loss": show_profit_loss,
    "Refund": show_refund,
    "User Management": show_user_management,   # ✅ ADD THIS
}

    current_menu = st.session_state.get("menu")

    # fallback logic (IMPORTANT FIX)
    current_menu = st.session_state.get("menu", "POS System")

if current_menu not in menu_map:
    # ❌ auto fallback မလုပ်ပါနဲ့
    st.error(f"Menu not found: {current_menu}")
    current_menu = "POS System"

    menu_map[current_menu]()

    # --------------------------
    # AUTO SYNC AFTER LOGIN
    # --------------------------
    auto_sync_on_start()

    # --------------------------
    # RECEIPT VIEW
    # --------------------------
    if st.session_state.get("receipt"):

        show_receipt(
            data=st.session_state.receipt,
            totals=st.session_state.receipt_totals,
            receipt_no=st.session_state.get("receipt_no", "N/A"),
            payment_method=st.session_state.get("current_payment_method", "Cash"),
            customer=st.session_state.get("current_customer", "Walk-in")
        )

        if st.button("🧾 Close Receipt"):
            st.session_state.receipt = None
            st.session_state.receipt_totals = None
            st.rerun()


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    main()
