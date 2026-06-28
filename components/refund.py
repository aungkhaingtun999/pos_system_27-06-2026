import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # 1. State ရှင်းလင်းခြင်း
    if "current_refund_inv" not in st.session_state: 
        st.session_state.current_refund_inv = None
    if "msg" not in st.session_state: 
        st.session_state.msg = None

    if st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    # 2. Database မှ Data အသစ်ကို အမြဲဆွဲယူခြင်း
    try:
        response = supabase.table("sales").select("*").order("id", desc=True).execute()
        sales_data = response.data if response.data else []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return
    
    # 3. Selection UI
    options = {f"📄 {r.get('receipt_no')} {'[REFUNDED]' if r.get('status') == 'refunded' else ''}": r for r in sales_data}
    
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))
    
    if selected == "":
        st.session_state.current_refund_inv = None
    else:
        st.session_state.current_refund_inv = options[selected]

    inv = st.session_state.current_refund_inv
    
    # 4. Refund Process
    if inv:
        # Database မှ နောက်ဆုံး status ကို တိုက်ရိုက်ပြန်စစ်ပါ
        check_status = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
        
        if check_status and check_status.get('status') == 'refunded':
            st.error("⚠️ ဤပြေစာသည် ယခင်ကပင် Refund လုပ်ပြီးသားဖြစ်ပါသည်။")
            if st.button("ပြန်လည်ရွေးချယ်မည်"):
                st.session_state.current_refund_inv = None
                st.rerun()
        else:
            st.subheader(f"📋 Items in {inv.get('receipt_no')}")
            items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])

            with st.form("refund_form"):
                selected_refund_items = []
                total_refund_value = 0
                
                # Header row
                c1, c2, c3, c4 = st.columns([0.4, 0.2, 0.2, 0.2])
                c1.write("**Item**")
                c2.write("**Qty**")
                c3.write("**Price**")
                c4.write("**Total**")

                for i, item in enumerate(items):
                    price = float(item.get('sell_price') or item.get('price') or 0)
                    qty = int(item.get('qty', 1))
                    item_total = price * qty
                    
                    col1, col2, col3, col4 = st.columns([0.4, 0.2, 0.2, 0.2])
                    is_checked = col1.checkbox(f"{item.get('product_name', 'Item')}", key=f"chk_{i}")
                    col2.write(f"{qty}")
                    col3.write(f"{price:,.0f}")
                    col4.write(f"{item_total:,.0f}")
                    
                    if is_checked:
                        selected_refund_items.append(item)
                        total_refund_value += item_total
                
                st.write("---")
                st.write(f"### 💰 Total Refund Amount: {total_refund_value:,.2f} MMK")
                submitted = st.form_submit_button("⚠️ Confirm Process Refund")
                
                if submitted:
                    if not selected_refund_items:
                        st.warning("Please select at least one item.")
                    else:
                        try:
                            processed_amount = execute_refund(inv, selected_refund_items)
                            st.session_state.msg = f"✅ Refund of {processed_amount:,.2f} MMK processed successfully!"
                            st.session_state.current_refund_inv = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Refund Error: {e}")

        if st.button("❌ Close"):
            st.session_state.current_refund_inv = None
            st.rerun()
