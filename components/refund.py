import streamlit as st
import json
from components.supabase_logic import supabase, execute_refund

def safe_float(value):
    try:
        if value is None: return 0.0
        if isinstance(value, str): value = value.replace(",", "")
        return float(value)
    except:
        return 0.0

def show_refund():
    st.title("🔄 Refund Manager")

    # Message Handling
    if "msg" in st.session_state and st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None

    # Load Sales
    try:
        response = supabase.table("sales").select("*").order("id", desc=True).execute()
        sales_data = response.data or []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    if not sales_data:
        st.info("No sales record found.")
        return

    # Receipt Select
    options = {f"📄 {r.get('receipt_no', '-')} {'[REFUNDED]' if r.get('status') == 'refunded' else ''}": r for r in sales_data}
    selected = st.selectbox("🔍 Select Receipt to Refund:", [""] + list(options.keys()))

    if not selected:
        return

    inv = options[selected]

    if inv.get("status") == "refunded":
        st.error("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်ပါသည်။")
        return

    # Load Items
    raw_items = inv.get("item", [])
    items = json.loads(raw_items) if isinstance(raw_items, str) else raw_items

    st.subheader(f"📋 Items in {inv.get('receipt_no')}")

    selected_items = []
    refund_total = 0.0

    # Item Selection
    for i, item in enumerate(items):
        product_name = item.get("product_name", "Unknown")
        qty = int(item.get("qty", 1))
        sell_price = safe_float(item.get("sell_price") or item.get("price") or 0)
        
        col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
        checked = col1.checkbox(f"{product_name}", key=f"ref_{inv['id']}_{i}")
        col2.write(f"Qty : {qty}")
        col3.write(f"{sell_price:,.2f} MMK")

        if checked:
            selected_items.append(item)
            refund_total += (sell_price * qty)

    st.divider()
    st.subheader(f"💰 Refund Amount : {refund_total:,.2f} MMK")

    # Confirm Button
    if st.button("⚠️ Confirm Process Refund", type="primary"):
        if not selected_items:
            st.warning("Please select at least one item.")
        else:
            try:
                # Double Check Status
                check = supabase.table("sales").select("status").eq("id", inv["id"]).single().execute()
                if check.data and check.data.get("status") == "refunded":
                    st.error("❌ Already refunded.")
                else:
                    # Execute Refund
                    processed = execute_refund(inv, selected_items, refund_total)
                    st.session_state.msg = f"✅ Refund {processed:,.2f} MMK completed!"
                    st.rerun()
            except Exception as e:
                st.error(f"Refund Error: {e}")
