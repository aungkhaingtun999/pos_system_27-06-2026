import streamlit as st
import json
import pandas as pd
from datetime import datetime
from database import get_sales
from products import get_products_cached
from config import APP_SETTINGS

# ==========================================
# 2. Helper Functions (Advanced Calculation)
# ==========================================
def _calculate_profit_by_date(sales, products, start_date, end_date):
    total_sales = 0
    total_cost = 0
    filtered_sales_list = []
    product_map = {str(p.get('barcode')): p for p in products}
    
    for sale in sales:
        # sales schema: (id, receipt_no, sale_date, items, totals, ...)
        sale_date_raw = pd.to_datetime(sale[2]).date()
        
        # ရက်စွဲ Filter လုပ်ခြင်း
        if start_date <= sale_date_raw <= end_date:
            items_json = sale[3]
            totals_json = sale[4]
            
            try:
                items_data = json.loads(items_json) if isinstance(items_json, str) else items_json
                totals_data = json.loads(totals_json) if isinstance(totals_json, str) else totals_json
                if isinstance(totals_data, list): totals_data = totals_data[0]
                
                grand_total = float(totals_data.get("grand_total", 0))
                total_sales += grand_total
                
                # Cost တွက်ခြင်း
                for item in items_data:
                    barcode = str(item.get('barcode'))
                    qty = int(item.get('qty', 1))
                    prod = product_map.get(barcode, {})
                    buy_price = float(prod.get('buy_price', 0))
                    total_cost += (buy_price * qty)
                
                # Table အတွက် စုဆောင်းခြင်း
                filtered_sales_list.append({
                    "ပြေစာအမှတ်": sale[1],
                    "ရက်စွဲ": sale[2],
                    "စုစုပေါင်း (MMK)": grand_total,
                    "ပေးချေမှု": totals_data.get("payment_method", "Cash")
                })
            except Exception:
                continue
                
    return total_sales, total_cost, filtered_sales_list

# ==========================================
# 3. Main Run Module (Profit & Loss UI)
# ==========================================
def show_profit_loss():
    st.title("📈 Profit & Loss Report")

    # 1. Date Selection UI
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Start Date", value=datetime.now().date())
    end_date = col_b.date_input("End Date", value=datetime.now().date())

    # 2. Data Fetching
    sales = get_sales()
    products = get_products_cached()
    
    if not sales:
        st.info("လက်ရှိတွင် အရောင်းမှတ်တမ်း မရှိသေးပါ။")
        return

    # 3. Calculations
    total_sales, total_cost, filtered_sales = _calculate_profit_by_date(sales, products, start_date, end_date)
    net_profit = total_sales - total_cost

    # 4. Display Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 ရောင်းရငွေ (Sales)", f"{total_sales:,.0f} {APP_SETTINGS['currency']}")
    col2.metric("📉 ကုန်ကျစရိတ် (Cost)", f"{total_cost:,.0f} {APP_SETTINGS['currency']}")
    col3.metric("📊 အမြတ် (Profit)", f"{net_profit:,.0f} {APP_SETTINGS['currency']}")

    st.markdown("---")
    st.write("### 📝 အရောင်းမှတ်တမ်းအသေးစိတ်")
    
    if filtered_sales:
        df = pd.DataFrame(filtered_sales)
        st.dataframe(
            df, 
            column_config={
                "စုစုပေါင်း (MMK)": st.column_config.NumberColumn("စုစုပေါင်း (MMK)", format="%.0f"),
            },
            use_container_width=True
        )
    else:
        st.warning("ရွေးချယ်ထားသော ရက်စွဲများအတွင်း အရောင်းမှတ်တမ်း မတွေ့ရှိပါ။")
