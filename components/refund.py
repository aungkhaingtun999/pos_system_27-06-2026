import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # Session State ရှင်းလင်းခြင်း
    if "current_refund_inv" not in st.session_state: 
        st.session_state.current_refund_inv = None

    # Database မှ Data အသစ်ကို ချက်ချင်းပြန်ဆွဲယူခြင်း
    try:
        response = supabase.table("sales").select("*").order("id", desc=True).execute()
        sales_data = response.data if response.data else []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return
    
    # Select Box (Refunded ဖြစ်ပြီးသားများကို ရှောင်ဖို့ စစ်ဆေးထား)
    options = {f"📄 {r.get('receipt_no')} {'[REFUNDED]' if r.get('status') == 'refunded' else ''}": r for r in sales_data}
    
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))
    
    # အသစ်ရွေးလိုက်တိုင်း Session State ကို Update လုပ်ပေးခြင်း
    if selected and selected != "":
        st.session_state.current_refund_inv = options[selected]
    elif selected == "":
        st.session_state.current_refund_inv = None

    inv = st.session_state.current_refund_inv
    
    if inv:
        # [အရေးကြီး] Database မှ လက်ရှိ Status ကို ချက်ချင်းပြန်စစ်ပါ (Cache မသုံးပါ)
        current_status = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
        
        if current_status and current_status.get('status') == 'refunded':
            st.error("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")
            if st.button("ပြန်လည်ရွေးချယ်မည်"):
                st.session_state.current_refund_inv = None
                st.rerun()
        else:
            # Refund Form ပြသခြင်း
            items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])
            
            with st.form("refund_form"):
                selected_items = []
                for i, item in enumerate(items):
                    # Checkbox
                    if st.checkbox(f"{item.get('product_name', 'Item')} (x{item.get('qty')})", key=f"chk_{i}"):
                        selected_items.append(item)
                
                submitted = st.form_submit_button("⚠️ Confirm Process Refund")
                
                if submitted:
                    if not selected_items:
                        st.warning("Please select items.")
                    else:
                        try:
                            # execute_refund ထဲတွင် တင်းကျပ်သော Check ပါပြီးသားဖြစ်၍ 
                            # error တက်လျှင် မလုပ်ဆောင်ပါ။
                            processed_amount = execute_refund(inv, selected_items)
                            st.success(f"✅ Success! Refund: {processed_amount:,.2f} MMK")
                            st.session_state.current_refund_inv = None # Reset
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
