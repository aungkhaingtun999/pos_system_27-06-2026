import streamlit as st
import pandas as pd
import json
from datetime import datetime
from components.supabase_logic import supabase

def show_reports():
    st.title("📊 Sales & Refund Detailed Report")
    
    # 1. Date Selection UI
    col1, col2, col3 = st.columns([2, 2, 1])
    start_date = col1.date_input("Start Date", value=datetime.now().date())
    end_date = col2.date_input("End Date", value=datetime.now().date())
    view_type = col3.selectbox("Report အမျိုးအစား:", ["ရက်ချုပ်", "လချုပ်", "နှစ်ချုပ်"])
    
    # 2. Database မှ Data အားလုံးဆွဲထုတ်ခြင်း (Query ပြဿနာဖြေရှင်းရန်)
    try:
        response = supabase.table("sales").select("*").execute()
        report = response.data # List of dictionaries
        
        refund_resp = supabase.table("refunds").select("*").execute()
        refunds = refund_resp.data or []
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    # 3. Data Processing & Filtering
    sales_list = []
    for r in report:
        # created_at ကို datetime object ပြောင်း
        sale_date = pd.to_datetime(r['created_at']).date()
        
        # ရက်စွဲအကွာအဝေးအတွင်း ရှိမရှိ စစ်ဆေးခြင်း
        if start_date <= sale_date <= end_date:
            totals = json.loads(r['totals']) if isinstance(r['totals'], str) else r['totals']
            sales_list.append({
                "Date": pd.to_datetime(r['created_at']),
                "Receipt": str(r['receipt_no']),
                "Item Total": float(totals.get("subtotal", 0)),
                "Tax": float(totals.get("tax", 0)),
                "Discount": float(totals.get("discount", 0)),
                "Grand Total": float(totals.get("grand_total", 0)),
                "Type": "Sale",
                "Raw": r
            })

    df_sales = pd.DataFrame(sales_list)

    # 4. Display Report
    if not df_sales.empty:
        st.subheader(f"📋 Sales Records ({start_date} to {end_date})")
        
        # ဇယားကွက်ပြသခြင်း
        display_df = df_sales[['Date', 'Receipt', 'Item Total', 'Tax', 'Discount', 'Grand Total']]
        st.dataframe(display_df.style.format({
            "Item Total": "{:,.2f}", "Tax": "{:,.2f}", 
            "Discount": "{:,.2f}", "Grand Total": "{:,.2f}"
        }), use_container_width=True)
        
        # Metric တွက်ချက်ခြင်း
        total_sales = df_sales['Grand Total'].sum()
        total_refund = sum([-float(r.get("refund_amount", 0)) for r in refunds 
                           if start_date <= pd.to_datetime(r['refunded_at']).date() <= end_date])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 ရောင်းရငွေ", f"{total_sales:,.2f} MMK")
        c2.metric("🔄 Refund", f"{abs(total_refund):,.2f} MMK")
        c3.metric("🎯 အသားတင်ရငွေ", f"{(total_sales + total_refund):,.2f} MMK")
    else:
        st.info("ရွေးချယ်ထားသော ရက်စွဲများအတွင်း အရောင်းစာရင်း မရှိပါ။")

    # 5. Reprint Receipt Section
    st.markdown("---")
    st.subheader("🖨️ Reprint Receipt")
    if not df_sales.empty:
        receipt_options = {f"Receipt #{d['Receipt']} ({d['Date'].strftime('%Y-%m-%d %H:%M')})": d for d in sales_list}
        selected = st.selectbox("Receipt ရွေးပါ:", list(receipt_options.keys()))
        
        if st.button("Print Selected Receipt"):
            selected_data = receipt_options[selected]
            row = selected_data["Raw"]
            
            # Session State အသစ်တင်ခြင်း (Typo များ ပြင်ထားသည်)
            st.session_state.receipt = json.loads(row['item']) if isinstance(row['item'], str) else row['item']
            st.session_state.receipt_totals = json.loads(row['totals']) if isinstance(row['totals'], str) else row['totals']
            st.session_state.receipt_no = row['receipt_no']
            st.session_state.menu = "POS System"
            st.session_state.is_reprint = True
            st.rerun()
