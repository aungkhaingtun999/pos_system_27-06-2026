import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # Session States initialization
    if "current_refund_inv" not in st.session_state: st.session_state.current_refund_inv = None
    if "msg" not in st.session_state: st.session_state.msg = None

    if st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    # Fetching sales data
    sales_data = supabase.table("sales").select("*").order("id", desc=True).execute().data or []
    
    # Selection Menu
    options = {f"📄 {r.get('receipt_no')} {'(Refunded)' if r.get('status') == 'refunded' else ''}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt:", [""] + list(options.keys()))
    
    if selected:
        st.session_state.current_refund_inv = options[selected]
    
    inv = st.session_state.current_refund_inv
    
    if inv:
        # Check Status
        if inv.get('status') == 'refunded':
            st.error("⚠️ ဤပြေစာသည် ယခင်ကပင် Refund လုပ်ပြီးသားဖြစ်ပါသည်။")
        else:
            st.subheader(f"📋 Items in {inv.get('receipt_no')}")
            items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])

            with st.form("refund_form"):
                selected_refund_items = []
                total_refund_value = 0
                
                for i, item in enumerate(items):
                    # Price calculation (sell_price ကို ဦးစားပေး)
                    price = float(item.get('sell_price') or item.get('price') or 0)
                    qty = int(item.get('qty', 1))
                    item_total = price * qty
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    is_checked = col1.checkbox(f"{item.get('product_name', 'Item')} (x{qty})", key=f"chk_{i}")
                    col2.write(f"@{price:,.2f}")
                    col3.write(f"**{item_total:,.2f}**")
                    
                    if is_checked:
                        selected_refund_items.append({**item, 'qty': qty, 'price': price})
                        total_refund_value += item_total

                st.write(f"### 💰 Refund Total: {total_refund_value:,.2f} MMK")
                submitted = st.form_submit_button("⚠️ Process Refund")
                
                if submitted:
                    if selected_refund_items:
                        try:
                            # execute_refund ထဲမှာတင် status update နဲ့ refund log အားလုံးပါပြီးသားဖြစ်ပါတယ်
                            processed_amount = execute_refund(inv, selected_refund_items)
                            
                            st.session_state.msg = f"✅ Refund of {processed_amount:,.2f} MMK processed successfully!"
                            st.session_state.current_refund_inv = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database Error: {e}")
                    else:
                        st.warning("Please select at least one item to refund.")

        st.divider()
        if st.button("❌ Exit"):
            st.session_state.current_refund_inv = None
            st.rerun()
