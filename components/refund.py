import streamlit as st
import json
from components.supabase_logic import supabase

def show_refund():
    st.title("🔄 Refund Manager")

    # Session States
    if "current_refund_inv" not in st.session_state: st.session_state.current_refund_inv = None
    if "msg" not in st.session_state: st.session_state.msg = None

    # Message Display
    if st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    # Fetch Sales Data
    sales_data = supabase.table("sales").select("*").order("id", desc=True).execute().data or []
    
    options = {f"📄 {r.get('receipt_no')}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt:", [""] + list(options.keys()))
    
    if selected:
        st.session_state.current_refund_inv = options[selected]
    
    inv = st.session_state.current_refund_inv
    
    if inv:
        st.subheader(f"📋 Items in {inv.get('receipt_no')}")
        items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])

        # Refund Form
        with st.form("refund_form"):
            selected_refund_items = []
            total_refund_value = 0
            
            for i, item in enumerate(items):
                # [ပြင်ဆင်ချက်] sell_price ကို ဦးစားပေးခေါ်ယူခြင်း
                price = float(item.get('sell_price') or item.get('price') or 0)
                qty = int(item.get('qty', 1))
                item_total = price * qty
                
                # Layout for Item Display
                col1, col2, col3 = st.columns([3, 1, 1])
                is_checked = col1.checkbox(f"{item.get('product_name', 'Item')} (x{qty})", key=f"chk_{i}")
                col2.write(f"@{price:,.2f}")
                col3.write(f"**{item_total:,.2f}**")
                
                if is_checked:
                    selected_refund_items.append(item)
                    total_refund_value += item_total

            st.write(f"### 💰 Refund Total: {total_refund_value:,.2f} MMK")
            submitted = st.form_submit_button("⚠️ Process Refund")
            
            if submitted:
                if selected_refund_items:
                    # [ဒီနေရာတွင် သင်၏ refund လုပ်ဆောင်ချက်များကို ထည့်သွင်းပါ]
                    # ဥပမာ: log_refund(inv['id'], selected_refund_items, total_refund_value)
                    st.session_state.msg = f"✅ Refund of {total_refund_value:,.2f} MMK processed successfully!"
                    st.rerun()
                else:
                    st.warning("Please select at least one item to refund.")

        st.divider()
        
        # Actions
        col1, col2 = st.columns(2)
        if col1.button("🚫 Void Entire Receipt"):
            supabase.table("sales").delete().eq("id", inv['id']).execute()
            st.session_state.msg = "⚠️ Receipt voided!"
            st.session_state.current_refund_inv = None
            st.rerun()
            
        if col2.button("❌ Exit"):
            st.session_state.current_refund_inv = None
            st.rerun()
