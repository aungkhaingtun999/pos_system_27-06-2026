import sys
import os
# လက်ရှိ folder ကို path ထဲထည့်ခြင်း
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
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

def setup_page():
    st.set_page_config(page_title="Barcode POS System", layout="wide", initial_sidebar_state="expanded")

def auto_sync_on_start():
    """App စဖွင့်သည်နှင့် Internet ရှိပါက Pending Sales များကို Cloud သို့ Sync လုပ်ခြင်း"""
    if "pending_sales" in st.session_state and st.session_state.pending_sales:
        with st.spinner("🌐 Cloud နှင့် ချိတ်ဆက်နေသည်..."):
            for sale in list(st.session_state.pending_sales):
                try:
                    insert_sale_to_supabase(sale['cart'], sale['totals'], sale['rec_no'], sale['payment_method'], sale['customer'])
                    st.session_state.pending_sales.remove(sale)
                except Exception as e:
                    st.warning("အင်တာနက် အားနည်းနေ၍ Sync မအောင်မြင်ပါ။ နောက်မှ ထပ်ကြိုးစားပါမည်။")
                    break

def run_router():
    menu_map = {
        "POS System": show_pos_system,
        "Inventory": show_inventory,
        "Reports": show_reports,
        "Profit & Loss": show_profit_loss, 
        "Refund": show_refund,
    }
    current_menu = st.session_state.get("menu", "POS System")
    menu_map.get(current_menu, show_pos_system)()

def main():
    setup_page()
    init_auth_state()
    init_app_state()
    init_session()

    if not check_password(): 
        st.stop()
        
    # App စဖွင့်ချိန် Auto Sync လုပ်ခြင်း
    auto_sync_on_start()
    
    show_sidebar()
    run_router()

    # --- Receipt Logic ---
    if st.session_state.get("receipt") is not None:
        show_receipt(
            data=st.session_state.receipt,
            totals=st.session_state.receipt_totals,
            receipt_no=st.session_state.get("receipt_no", "N/A"),
            payment_method=st.session_state.get("current_payment_method", "Cash"),
            customer=st.session_state.get("current_customer", "Walk-in")
        )
        
        # Receipt ပြပြီးလျှင် Session ကို ပြန်လည်ရှင်းလင်းခြင်း (အရေးကြီး)
        if st.button("Close Receipt"):
            st.session_state.receipt = None
            st.session_state.receipt_totals = None
            st.rerun()

if __name__ == "__main__":
    main()
