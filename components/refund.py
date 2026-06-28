import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # Database မှ Data ဆွဲယူခြင်း
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
        # Items Data ကို ဆွဲယူခြင်း
        raw_items = inv.get('item', '[]')
        items = json.loads(raw_items) if isinstance(raw_items, str) else raw_items
        
        st.subheader(f"📋 Items in {inv.get('receipt_no')}")
        
        selected_refund_items = []
        total_refund_value = 0.0
        
        for i, item in enumerate(items):
            # Key များကို စစ်ဆေးပါ (Sell_price မရှိလျှင် price ကို ယူသည်)
            price = float(item.get('sell_price') or item.get('price') or 0)
            qty = int(item.get('qty', 1))
            
            # Checkbox ပြသခြင်း
            is_checked = st.checkbox(
                f"{item.get('product_name', 'Item')} | Qty: {qty} | Price: {price:,.0f} MMK", 
                key=f"chk_{i}"
            )
            
            if is_checked:
                selected_refund_items.append(item)
                total_refund_value += (price * qty)
        
        st.write(f"### 💰 Total Refund Amount: {total_refund_value:,.2f} MMK")
        
        if st.button("⚠️ Confirm Process Refund"):
            if not selected_refund_items:
                st.warning("အနည်းဆုံး Item တစ်ခု ရွေးပေးပါ။")
            else:
                try:
                    processed = execute_refund(inv, selected_refund_items)
                    st.success(f"✅ Refund {processed:,.2f} MMK processed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Refund Error: {e}")
