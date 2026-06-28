import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # Message ရှင်းလင်းခြင်း
    if "msg" in st.session_state and st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    # Database Data ဆွဲယူခြင်း
    try:
        response = supabase.table("sales").select("*").order("id", desc=True).execute()
        sales_data = response.data if response.data else []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return
    
    options = {f"📄 {r.get('receipt_no')} {'[REFUNDED]' if r.get('status') == 'refunded' else ''}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))
    inv = options.get(selected) if selected else None

    if inv:
        if inv.get('status') == 'refunded':
            st.error("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")
        else:
            items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])
            
            st.subheader(f"📋 Items in {inv.get('receipt_no')}")
            
            # Form မစခင် Checkbox state ကို စစ်ဆေးပါ
            with st.form("refund_form"):
                total_refund_value = 0
                selected_refund_items = []
                
                for i, item in enumerate(items):
                    price = float(item.get('sell_price') or item.get('price') or 0)
                    qty = int(item.get('qty', 1))
                    
                    # Checkbox တိုင်းကို unique key ပေးထားပါ
                    is_checked = st.checkbox(f"{item.get('product_name')} | Qty: {qty} | Price: {price:,.0f}", key=f"chk_{inv['id']}_{i}")
                    
                    if is_checked:
                        selected_refund_items.append(item)
                        total_refund_value += (price * qty)
                
                st.write("---")
                st.write(f"### 💰 Total Refund Amount: {total_refund_value:,.2f} MMK")
                
                submitted = st.form_submit_button("⚠️ Confirm Process Refund")
                
                if submitted:
                    if not selected_refund_items:
                        st.warning("အနည်းဆုံး Item တစ်ခု ရွေးချယ်ပေးပါ။")
                    else:
                        try:
                            # နောက်ဆုံး Status ထပ်စစ် (Double Verification)
                            check = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
                            if check and check.get("status") == "refunded":
                                st.error("❌ ဤပြေစာကို Refund လုပ်ပြီးသွားပါပြီ။")
                            else:
                                processed = execute_refund(inv, selected_refund_items)
                                st.session_state.msg = f"✅ Refund {processed:,.2f} MMK processed!"
                                st.rerun() 
                        except Exception as e:
                            st.error(f"Refund Error: {e}")
