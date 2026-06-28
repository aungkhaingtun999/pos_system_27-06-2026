import streamlit as st
import json
import pandas as pd
from datetime import datetime
from database import get_sales
from products import get_products_cached
from config import APP_SETTINGS

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

    # 3. Processing and Filtering (Data များကို သေချာစွာ စစ်ထုတ်ခြင်း)
    total_sales = 0
    total_cost = 0
    filtered_sales = []
    product_map = {str(p.get('barcode')): p for p in products}

    for sale in sales:
        # sale[2] သည် ရက်စွဲဖြစ်သည်ဟု ယူဆသည် (ရက်စွဲဖော်မတ်ကို သေချာအောင်လုပ်ပါ)
        raw_date = pd.to_datetime(sale[2])
        sale_date = raw_date.date()

        # ရက်စွဲစစ်ခြင်း (Start Date <= Sale Date <= End Date)
        if start_date <= sale_date <= end_date:
            try:
                items_data = json.loads(sale[3]) if isinstance(sale[3], str) else sale[3]
                totals_data = json.loads(sale[4]) if isinstance(sale[4], str) else sale[4]
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
                filtered_sales.append({
                    "ပြေစာအမှတ်": sale[1],
                    "ရက်စွဲ": raw_date.strftime('%Y-%m-%d %H:%M'), # DateTime ကို String ပြောင်းပြခြင်း
                    "စုစုပေါင်း (MMK)": grand_total,
                    "ပေးချေမှု": totals_data.get("payment_method", "Cash")
                })
            except Exception:
                continue

    # 4. Display Metrics
    net_profit = total_sales - total_cost
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 ရောင်းရငွေ (Sales)", f"{total_sales:,.0f} {APP_SETTINGS['currency']}")
    col2.metric("📉 ကုန်ကျစရိတ် (Cost)", f"{total_cost:,.0f} {APP_SETTINGS['currency']}")
    col3.metric("📊 အမြတ် (Profit)", f"{net_profit:,.0f} {APP_SETTINGS['currency']}")

    st.markdown("---")
    st.write("### 📝 အရောင်းမှတ်တမ်းအသေးစိတ်")
    
    # 5. Display Table
    if filtered_sales:
        df = pd.DataFrame(filtered_sales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"ရွေးချယ်ထားသော {start_date} မှ {end_date} အတွင်း အရောင်းမှတ်တမ်း မတွေ့ရှိပါ။")
