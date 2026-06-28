import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database import get_report_by_date
from components.supabase_logic import supabase

def show_reports():
    st.title("📊 Sales & Refund Detailed Report")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    start_date = col1.date_input("Start Date", value=datetime.now().date())
    end_date = col2.date_input("End Date", value=datetime.now().date())
    view_type = col3.selectbox("Report အမျိုးအစား:", ["ရက်ချုပ်", "လချုပ်", "နှစ်ချုပ်"])
    
    # Database မှ Data ရယူခြင်း
    report = get_report_by_date(start_date, end_date)
    
    try:
        refunds = supabase.table("refunds").select("*").execute().data or []
    except: 
        refunds = []

    # 1. Sales Data Processing
    sales_list = []
    if isinstance(report, list):
        for r in report:
            # r[0]: id, r[1]: receipt_no, r[2]: created_at, r[3]: items, r[4]: totals
            if isinstance(r, (list, tuple)) and len(r) >= 5:
                totals = json.loads(r[4]) if isinstance(r[4], str) else r[4]
                sales_list.append({
                    "Date": pd.to_datetime(r[2]),
                    "Receipt": str(r[1]),
                    "Item Total": float(totals.get("subtotal", 0)),
                    "Tax": float(totals.get("tax", 0)),
                    "Discount": float(totals.get("discount", 0)),
                    "Grand Total": float(totals.get("grand_total", 0)),
                    "Type": "Sale",
                    "Amount": float(totals.get("grand_total", 0)),
                    "Raw": r
                })

    df_sales = pd.DataFrame(sales_list)

    # 2. Summary Report Display
    if not df_sales.empty:
        # ဇယားကွက်အတွက် Data ပြင်ဆင်ခြင်း
        st.subheader("📋 Sales Records")
        display_df = df_sales[['Date', 'Receipt', 'Item Total', 'Tax', 'Discount', 'Grand Total']]
        st.dataframe(display_df.style.format({
            "Item Total": "{:,.2f}", "Tax": "{:,.2f}", 
            "Discount": "{:,.2f}", "Grand Total": "{:,.2f}"
        }), use_container_width=True)
        
        # Metric ပြသခြင်း
        c1, c2, c3 = st.columns(3)
        total_sales = df_sales['Grand Total'].sum()
        total_refund = sum([-float(r.get("refund_amount", 0)) for r in refunds])
        
        c1.metric("💰 ရောင်းရငွေ", f"{total_sales:,.2f} MMK")
        c2.metric("🔄 Refund", f"{abs(total_refund):,.2f} MMK")
        c3.metric("🎯 အသားတင်ရငွေ", f"{(total_sales + total_refund):,.2f} MMK")
    else:
        st.info("ရွေးချယ်ထားသော ရက်စွဲတွင် အရောင်းစာရင်း မရှိပါ။")

    # 3. Reprint Receipt Section
    st.markdown("---")
    st.subheader("🖨️ Reprint Receipt")
    if not df_sales.empty:
        receipt_options = {f"Receipt #{d['Receipt']} ({d['Date'].strftime('%Y-%m-%d %H:%M')})": d for d in sales_list}
        selected = st.selectbox("Receipt ရွေးပါ:", list(receipt_options.keys()))
        
        if st.button("Print Selected Receipt"):
            selected_data = receipt_options[selected]
            row = selected_data["Raw"]
            
            # POS System သို့ Data ပို့ခြင်း
            st.session_state.receipt = json.loads(row[3]) if isinstance(row[3], str) else row[3]
            st.session_state.receipt_totals = json.loads(row[4]) if isinstance(row[4], str) else row[4]
            st.session_state.receipt_no = row[1]
            st.session_state.menu = "POS System"
            st.session_state.is_reprint = True
            st.rerun()
