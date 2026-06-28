import sys
import os
import streamlit as st

# Root directory path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Modules
from auth import check_password, init_auth_state
from utils import init_app_state
from config import init_session
from components.supabase_logic import sync_to_supabase # Sync function ကို အပေါ်မှာ သေချာ import လုပ်ပါ
from components.sidebar import show_sidebar
from components.pos_system import show_pos_system
from components.reports import show_reports
from components.inventory import show_inventory
from components.profit_loss import show_profit_loss
from components.refund import show_refund
from components.receipt import show_receipt

def setup_page():
    # setup_page မှာ st.set_page_config ကို တစ်ကြိမ်သာ ခေါ်ရပါမယ်
    if "page_config_set" not in st.session_state:
        st.set_page_config(page_title="Barcode POS System", layout="wide")
        st.session_state.page_config_set = True

def auto_sync_on_start():
    # session_state ထဲက pending_sales ကိုယူပါ
    pending_data = st.session_state.get("pending_sales", [])
    
    # Data ရှိမှသာ Sync လုပ်ပါ
    if pending_data and isinstance(pending_data, list) and len(pending_data) > 0:
        try:
            # Argument အနေနဲ့ pending_data ကို ပို့ပေးလိုက်ပါ
            sync_to_supabase(pending_data)
            
            # Sync အောင်မြင်မှသာ ရှင်းပါ
            st.session_state.pending_sales = []
            st.success("✅ Cloud နှင့် Sync အောင်မြင်ပါသည်။")
        except Exception as e:
            st.error(f"Sync Failed: {e}")

def main():
    setup_page()
    init_auth_state()
    init_app_state()
    init_session()

    # Authentication
    if not check_password(): 
        st.stop()
    
    # Sync လုပ်ဆောင်ခြင်း
    auto_sync_on_start()
    
    # Sidebar
    show_sidebar()
    
    # Page Router
    menu_map = {
        "POS System": show_pos_system,
        "Inventory": show_inventory,
        "Reports": show_reports,
        "Profit & Loss": show_profit_loss, 
        "Refund": show_refund,
    }
    
    current_menu = st.session_state.get("menu", "POS System")
    menu_map.get(current_menu, show_pos_system)()

    # Receipt Logic
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
