import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # Message ပြသခြင်း
    if "msg" in st.session_state and st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    try:
        response = supabase.table("sales").select("*").order("id", desc=True).execute()
        sales_data = response.data if response.data else []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return
    
    options = {f"📄 {r.get('receipt_no')}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))
    inv = options.get(selected) if selected else None

    if inv:
        items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])
        
        # Checkbox များကို သိမ်းရန်အတွက် dict တစ်ခုအသုံးပြုပါ
        if "refund_checkboxes" not in st.session_state:
            st.session_state.refund_checkboxes = {}

        st.subheader(f"📋 Items in {inv.get('receipt_no')}")
        
        total_refund_value = 0
        selected_refund_items = []
        
        # Checkbox များ ဆောက်လုပ်ခြင်း
        for i, item in enumerate(items):
            key = f"chk_{inv['id']}_{i}"
            # Checkbox အမှန်ခြစ်ကို session_state တွင် သိမ်းပါ
            is_checked = st.checkbox(f"{item.get('product_name', 'Item')} - {float(item.get('price', 0)):,.0f} MMK", key=key)
            
            if is_checked:
                selected_refund_items.append(item)
                total_refund_value += float(item.get('price', 0)) * int(item.get('qty', 1))
        
        st.write(f"### 💰 Total Refund Amount: {total_refund_value:,.2f} MMK")
        
        if st.button("⚠️ Confirm Process Refund"):
            if not selected_refund_items:
                st.warning("အနည်းဆုံး Item တစ်ခု ရွေးချယ်ပေးပါ။")
            else:
                try:
                    processed = execute_refund(inv, selected_refund_items)
                    st.session_state.msg = f"✅ Refund {processed:,.2f} MMK processed!"
                    st.rerun()
                except Exception as e:
                    st.error(f"Refund Error: {e}")
