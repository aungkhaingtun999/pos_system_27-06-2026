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
        sales_data = supabase.table("sales").select("*").execute().data or []
        products_data = supabase.table("products").select("*").execute().data or []
        product_map = {str(p.get('barcode')): p for p in products_data}
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    total_sales = 0
    total_cost = 0
    total_tax = 0
    total_discount = 0
    filtered_sales = []

    for sale in sales_data:
        raw_date = pd.to_datetime(sale.get('created_at'))
        if start_date <= raw_date.date() <= end_date:
            try:
                items = json.loads(sale.get('item', '[]'))
                totals = json.loads(sale.get('totals', '{}'))
                
                # Sales values
                grand_total = float(totals.get("grand_total", 0))
                total_sales += grand_total
                total_tax += float(totals.get("tax", 0))
                total_discount += float(totals.get("discount", 0))
                
                # Cost Calculation (Buy Price မှ တွက်ချက်)
                for item in items:
                    prod = product_map.get(str(item.get('barcode')), {})
                    # cost_price သို့မဟုတ် buy_price ကို စစ်ဆေးယူပါ
                    buy_price = float(prod.get('cost_price') or prod.get('buy_price') or 0)
                    total_cost += (buy_price * int(item.get('qty', 1)))
                
                filtered_sales.append({
                    "ပြေစာအမှတ်": sale.get('receipt_no'),
                    "ရက်စွဲ": raw_date.strftime('%Y-%m-%d'),
                    "Grand Total": grand_total
                })
            except: continue

    # Net Profit = Sales - Cost - Discount - Tax
    net_profit = total_sales - total_cost - total_discount - total_tax

    # Display Metrics
    st.subheader(f"📊 Summary ({start_date} to {end_date})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 ရောင်းရငွေ", f"{total_sales:,.0f}")
    c2.metric("📉 ကုန်ကျစရိတ်", f"{total_cost:,.0f}")
    c3.metric("🏷️ Discount/Tax", f"{(total_discount + total_tax):,.0f}")
    c4.metric("🎯 အသားတင်အမြတ်", f"{net_profit:,.0f}")

    st.write("---")
    if filtered_sales:
        st.dataframe(pd.DataFrame(filtered_sales), use_container_width=True)
