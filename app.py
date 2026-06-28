import sys
import os
import streamlit as st

# Root directory ကို Path ထဲသို့ သေချာထည့်ခြင်း
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Auth & Config
from auth import check_password, init_auth_state
from utils import init_app_state
from config import init_session

# Component များ import လုပ်ခြင်း
try:
    from components.sidebar import show_sidebar
    from components.pos_system import show_pos_system
    from components.reports import show_reports
    from components.inventory import show_inventory
    from components.profit_loss import show_profit_loss
    from components.refund import show_refund
    from components.receipt import show_receipt
    # Supabase Logic Import
    from components.supabase_logic import insert_sale, sync_to_supabase
except Exception as e:
    st.error(f"Module Import Error: {e}")
    st.stop()

def setup_page():
    st.set_page_config(
        page_title="Barcode POS System", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )

def auto_sync_on_start():
    """App စဖွင့်သည်နှင့် Internet ရှိပါက Pending Sales များကို Cloud သို့ Sync လုပ်ခြင်း"""
    if "pending_sales" in st.session_state and st.session_state.pending_sales:
        with st.spinner("🌐 Cloud နှင့် ချိတ်ဆက်နေသည်..."):
            try:
                # sync_to_supabase function ကို စာရင်းတစ်ခုလုံးပေး၍ ခေါ်ပါ
                sync_to_supabase(st.session_state.pending_sales)
                
                # အောင်မြင်ပါက Pending စာရင်းကို ရှင်းလင်းပါ
                st.session_state.pending_sales = []
                st.success("✅ အားလုံး Sync လုပ်ပြီးပါပြီ။")
            except Exception as e:
                st.warning(f"အင်တာနက် အားနည်းနေ၍ Sync မအောင်မြင်ပါ။ ({e})")

def run_router():
    """Menu ရွေးချယ်မှုအလိုက် Page ပြောင်းလဲခြင်း"""
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

    # Login စစ်ဆေးခြင်း
    if not check_password(): 
        st.stop()
        
    # App စဖွင့်ချိန် Auto Sync လုပ်ခြင်း
    auto_sync_on_start()
    
    # Sidebar ပြသခြင်း
    show_sidebar()
    
    # ရွေးချယ်ထားသော စာမျက်နှာကို ပြသခြင်း
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
        
        # Receipt ပြပြီးလျှင် Session ကို ပြန်လည်ရှင်းလင်းခြင်း
        if st.button("Close Receipt"):
            st.session_state.receipt = None
            st.session_state.receipt_totals = None
            st.rerun()

if __name__ == "__main__":
    main()
