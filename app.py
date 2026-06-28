import sys
import os
import streamlit as st
from components import supabase_logic 

# Root directory 
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import check_password, init_auth_state
from utils import init_app_state
from config import init_session
from components.sidebar import show_sidebar
from components.pos_system import show_pos_system
from components.reports import show_reports
from components.inventory import show_inventory
from components.profit_loss import show_profit_loss
from components.refund import show_refund
from components.receipt import show_receipt

def setup_page():
    st.set_page_config(page_title="Barcode POS System", layout="wide")

# app.py အတွင်းရှိ Auto Sync function
# app.py ၏ auto_sync_on_start function
from components.supabase_logic import sync_to_supabase

# app.py ၏ auto_sync_on_start()
def auto_sync_on_start():
    # 1. session_state ထဲမှာ pending_sales ရှိမရှိ စစ်ဆေးပါ
    pending_data = st.session_state.get("pending_sales", [])
    
    # 2. data ရှိနေမှသာ sync function ကို ခေါ်ပါ
    if pending_data and isinstance(pending_data, list):
        try:
            # function ကို ခေါ်တဲ့အခါ pending_data ကို Argument အဖြစ် ထည့်ပေးလိုက်ပါ
            sync_to_supabase(pending_data) 
            
            # 3. Sync ပြီးသွားရင် list ကို ရှင်းလင်းပေးပါ
            st.session_state.pending_sales = []
            st.success("✅ အားလုံး Sync လုပ်ပြီးပါပြီ။")
        except Exception as e:
            st.error(f"Sync Failed: {e}")
def main():
    setup_page()
    init_auth_state()
    init_app_state()
    init_session()

    if not check_password(): st.stop()
    
    auto_sync_on_start()
    show_sidebar()
    
    # Page Router
    menu_map = {
        "POS System": show_pos_system,
        "Inventory": show_inventory,
        "Reports": show_reports,
        "Profit & Loss": show_profit_loss, 
        "Refund": show_refund,
    }
    menu_map.get(st.session_state.get("menu", "POS System"), show_pos_system)()

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
