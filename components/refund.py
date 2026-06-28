import streamlit as st
import json
from datetime import datetime
import pytz
import sys
import os

# Path ပြဿနာဖြေရှင်းရန်
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Supabase Logic Import
try:
    from components.supabase_logic import supabase, execute_refund
except ImportError:
    # အကယ်၍ အထက်ပါ path မရလျှင် root ကို ပြန်ရှာခြင်း
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # Session State ရှင်းလင်းခြင်း
    if "msg" in st.session_state and st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    # Database မှ Data အသစ်ဆွဲယူခြင်း
    try:
        response = supabase.table("sales").select("*").order("id", desc=True).execute()
        sales_data = response.data if response.data else []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return
    
    # Receipt ရွေးချယ်မှု
    options = {f"📄 {r.get('receipt_no')} {'[REFUNDED]' if r.get('status') == 'refunded' else ''}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))
    
    inv = options.get(selected) if selected else None

    if inv:
        if inv.get('status') == 'refunded':
            st.error("⚠️ ဤပြေစာသည် ယခင်ကပင် Refund လုပ်ပြီးသားဖြစ်ပါသည်။")
        else:
            st.subheader(f"📋 Items in {inv.get('receipt_no')}")
            items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])

            with st.form("refund_form"):
                c1, c2, c3, c4 = st.columns([0.4, 0.2, 0.2, 0.2])
                c1.write("**Item**"); c2.write("**Qty**"); c3.write("**Price**"); c4.write("**Total**")

                selected_refund_items = []
                total_refund_value = 0
                
                for i, item in enumerate(items):
                    price = float(item.get('sell_price') or item.get('price') or 0)
                    qty = int(item.get('qty', 1))
                    item_total = price * qty
                    
                    col1, col2, col3, col4 = st.columns([0.4, 0.2, 0.2, 0.2])
                    if col1.checkbox(f"{item.get('product_name', 'Item')}", key=f"chk_{i}"):
                        selected_refund_items.append(item)
                        total_refund_value += item_total
                    col2.write(f"{qty}"); col3.write(f"{price:,.0f}"); col4.write(f"{item_total:,.0f}")
                
                st.write("---")
                st.write(f"### 💰 Total Refund Amount: {total_refund_value:,.2f} MMK")
                
                if st.form_submit_button("⚠️ Confirm Process Refund"):
                    if not selected_refund_items:
                        st.warning("Please select at least one item.")
                    else:
                        try:
                            # ဤနေရာတွင် logic က status ကို အရင် lock လုပ်ပါမည်
                            processed_amount = execute_refund(inv, selected_refund_items)
                            st.session_state.msg = f"✅ Refund {processed_amount:,.2f} MMK processed!"
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Refund Error: {e}")
