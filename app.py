import streamlit as st
import sys
import os

# Project root ကို sys.path တွင် ထည့်သွင်းခြင်း (Import Error များကို ဖြေရှင်းရန်)
# ဤနည်းသည် app.py သည်မည်သည့်နေရာတွင်ရှိနေစေကာမူ အမြစ် (root) ကို ရှာတွေ့စေပါမည်။
root_path = os.path.dirname(os.path.abspath(__file__))
if root_path not in sys.path:
    sys.path.append(root_path)

# Import Modules
from auth import check_password, init_auth_state
from utils import init_app_state
from config import init_session
from components.sidebar import show_sidebar
from components.pos_system import show_pos_system
from components.reports import show_reports
from components.inventory import show_inventory
from components.profit_loss import show_profit_loss
from components.refund import show_refund
from components.receipt_generator import show_receipt 
from components.supabase_logic import insert_sale_to_supabase
from components.user_management import show_user_management

def setup_page():
    st.set_page_config(
        page_title="Barcode POS System", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )

def auto_sync_on_start():
    """App စဖွင့်သည်နှင့် Pending Sales များကို Cloud သို့ Sync လုပ်ခြင်း"""
    if "pending_sales" in st.session_state and st.session_state.pending_sales:
        with st.spinner("🌐 Cloud နှင့် ချိတ်ဆက်နေသည်..."):
            for sale in list(st.session_state.pending_sales):
                try:
                    insert_sale_to_supabase(
                        sale['cart'], sale['totals'], 
                        sale['rec_no'], sale['payment_method'], 
                        sale['customer']
                    )
                    st.session_state.pending_sales.remove(sale)
                except Exception:
                    st.warning("အင်တာနက် အားနည်းနေ၍ Sync မအောင်မြင်ပါ။")
                    break

def run_router():
    """Role-based Navigation Router"""
    role = st.session_state.get("user_role", "Cashier")
    
    # Menu Mapping
    menu_map = {
        "POS System": show_pos_system,
        "Inventory": show_inventory,
        "Reports": show_reports,
        "Profit & Loss": show_profit_loss, 
        "Refund": show_refund,
        "User Management": show_user_management
    }
    
    current_menu = st.session_state.get("menu", "POS System")
    
    # Security Check
    if current_menu == "User Management" and role != "Admin":
        current_menu = "POS System"
        st.session_state.menu = "POS System"
    
    # Render Selected Component
    if current_menu in menu_map:
        menu_map[current_menu]()
    else:
        show_pos_system()

def main():
    setup_page()
    init_auth_state()
    init_app_state()
    init_session()

    # Login Logic
    if not check_password(): 
        st.stop()
        
    # Sync & Navigation
    auto_sync_on_start()
    show_sidebar()
    run_router()

    # Receipt Display Logic
    if st.session_state.get("receipt") is not None:
        show_receipt(
            data=st.session_state.receipt,
            totals=st.session_state.receipt_totals,
            receipt_no=st.session_state.get("receipt_no", "N/A"),
            payment_method=st.session_state.get("current_payment_method", "Cash"),
            customer=st.session_state.get("current_customer", "Walk-in")
        )
        
        if st.button("Close Receipt"):
            st.session_state.receipt = None
            st.session_state.receipt_totals = None
            st.rerun()

if __name__ == "__main__":
    main()
