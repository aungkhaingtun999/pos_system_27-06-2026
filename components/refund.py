import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # 1. State ရှင်းလင်းခြင်း
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
    
    # ရွေးချယ်မှုအတွက် Key တစ်ခုခုကို အမြဲ reset ချနိုင်ရန် လုပ်ဆောင်ခြင်း
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))
    
    if selected == "":
        st.session_state.current_refund_inv = None
    else:
        # Receipt ပြောင်းလိုက်တိုင်း State ကို အသစ် update လုပ်ပါ
        st.session_state.current_refund_inv = options[selected]

    inv = st.session_state.current_refund_inv
    
    # 4. Refund Process
    if inv:
        # [အရေးကြီး] Database မှ နောက်ဆုံး status ကို တိုက်ရိုက်ပြန်စစ်ပါ (Cache မသုံးပါ)
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
                for i, item in enumerate(items):
                    is_checked = st.checkbox(f"{item.get('product_name', 'Item')} (x{item.get('qty')})", key=f"chk_{i}")
                    if is_checked:
                        selected_refund_items.append(item)
                
                submitted = st.form_submit_button("⚠️ Confirm Process Refund")
                
                if submitted:
                    if not selected_refund_items:
                        st.warning("Please select at least one item.")
                    else:
                        try:
                            # [Logic] execute_refund ထဲတွင် တင်းကျပ်သော Check ပါပြီးသားဖြစ်သည်
                            processed_amount = execute_refund(inv, selected_refund_items)
                            
                            # အောင်မြင်ပါက State အားလုံးကို ရှင်းလင်းပြီးမှ Rerun လုပ်ပါ
                            st.session_state.msg = f"✅ Refund of {processed_amount:,.2f} MMK processed successfully!"
                            st.session_state.current_refund_inv = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Refund Error: {e}")

        # Close button
        if st.button("❌ Close"):
            st.session_state.current_refund_inv = None
            st.rerun()
