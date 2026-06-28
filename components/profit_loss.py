import streamlit as st
import json
import pandas as pd
from datetime import datetime
from components.supabase_logic import supabase
from config import APP_SETTINGS

def show_profit_loss():
    st.title("📈 Profit & Loss Report")

    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Start Date", value=datetime.now().date())
    end_date = col_b.date_input("End Date", value=datetime.now().date())

    try:
        # Data ဆွဲယူခြင်း
        sales_data = supabase.table("sales").select("*").execute().data or []
        products_data = supabase.table("products").select("*").execute().data or []
        expenses_data = supabase.table("expenses").select("*").execute().data or []
        
        product_map = {str(p.get('barcode')): p for p in products_data}
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    # 1. Sales & Cost Calculation
    total_sales = 0
    total_cogs = 0 # Cost of Goods Sold (ပစ္စည်းဝယ်ဈေး)
    total_tax = 0
    total_discount = 0
    filtered_sales = []

    for sale in sales_data:
        raw_date = pd.to_datetime(sale.get('created_at'))
        if start_date <= raw_date.date() <= end_date:
            try:
                items = json.loads(sale.get('item', '[]'))
                totals = json.loads(sale.get('totals', '{}'))
                
                grand_total = float(totals.get("grand_total", 0))
                total_sales += grand_total
                total_tax += float(totals.get("tax", 0))
                total_discount += float(totals.get("discount", 0))
                
                for item in items:
                    prod = product_map.get(str(item.get('barcode')), {})
                    buy_price = float(prod.get('cost_price') or prod.get('buy_price') or 0)
                    total_cogs += (buy_price * int(item.get('qty', 1)))
                
                filtered_sales.append({
                    "ပြေစာအမှတ်": sale.get('receipt_no'),
                    "ရက်စွဲ": raw_date.strftime('%Y-%m-%d'),
                    "Grand Total": grand_total
                })
            except: continue

    # 2. Operating Expenses Calculation
    total_expenses = 0
    for ex in expenses_data:
        ex_date = pd.to_datetime(ex.get('date')).date()
        if start_date <= ex_date <= end_date:
            total_expenses += float(ex.get('amount', 0))

    # Net Profit Calculation
    # Net Profit = Sales - COGS - Expenses - Discount - Tax
    total_cost = total_cogs + total_expenses
    net_profit = total_sales - total_cost - total_discount - total_tax

    # Display Metrics
    st.subheader(f"📊 Summary ({start_date} to {end_date})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 ရောင်းရငွေ", f"{total_sales:,.0f}")
    c2.metric("📉 ကုန်ပစ္စည်းဝယ်ဈေး", f"{total_cogs:,.0f}")
    c3.metric("🛠️ လည်ပတ်မှုစရိတ်", f"{total_expenses:,.0f}")
    c4.metric("🎯 အသားတင်အမြတ်", f"{net_profit:,.0f}")

    # Discount/Tax breakdown
    st.info(f"မှတ်ချက်။ ။ Discount/Tax စုစုပေါင်းမှာ { (total_discount + total_tax):,.0f} ဖြစ်ပါသည်။")

    st.write("---")
    st.write("### 📝 အရောင်းမှတ်တမ်းအသေးစိတ်")
    if filtered_sales:
        st.dataframe(pd.DataFrame(filtered_sales), use_container_width=True)
    else:
        st.warning("ရွေးချယ်ထားသော ရက်စွဲများအတွင်း အရောင်းမှတ်တမ်း မရှိပါ။")
