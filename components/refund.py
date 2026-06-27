import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund, log_refund

def show_refund():
    st.title("🔄 Refund Manager")

    # [အချက် ၁] Session တွေကို ကြိုတင်သတ်မှတ်ထားမှ Error မတက်မှာပါ
    if "current_refund_inv" not in st.session_state: st.session_state.current_refund_inv = None
    if "msg" not in st.session_state: st.session_state.msg = None

    # [အချက် ၂] Message ပြသခြင်း (အရေးကြီးပါတယ်)
    if st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None # ပြပြီးရင် ပြန်ရှင်းပေးပါ

    sales_data = supabase.table("sales").select("*").order("id", desc=True).execute().data
    
    options = {f"📄 {r.get('receipt_no')}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt:", [""] + list(options.keys()))
    if selected:
        st.session_state.current_refund_inv = options[selected]
    
    inv = st.session_state.current_refund_inv
    
    if inv:
        items = json.loads(inv.get('item', '[]')) if isinstance(inv.get('item'), str) else inv.get('item', [])

        # [အချက် ၃] Form အလုပ်လုပ်အောင် သေချာပြင်ထားပါတယ်
        with st.form("refund_form"):
            check_states = {i: st.checkbox(f"{item.get('product_name', 'Item')}") for i, item in enumerate(items)}
            submitted = st.form_submit_button("⚠️ Process Refund")
            
            if submitted:
                # Logic တစ်ခုခုလုပ်ပြီးရင် msg ထဲကို ထည့်လိုက်ပါ
                st.session_state.msg = "✅ Refund processed successfully!"
                st.rerun() # ဒါမှ message ကို အပေါ်မှာ ပြနိုင်မှာပါ

        st.divider()
        # [အချက် ၄] Button တွေ အလုပ်လုပ်အောင် လုပ်ဆောင်ချက်တွေကို ခွဲထားပါတယ်
        if st.button("🚫 Void Entire Receipt"):
            supabase.table("sales").delete().eq("id", inv['id']).execute()
            st.session_state.msg = "⚠️ Receipt voided!"
            st.session_state.current_refund_inv = None
            st.rerun()
            
        if st.button("❌ Exit"):
            st.session_state.current_refund_inv = None
            st.rerun()