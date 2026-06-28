import streamlit as st
import json
import pandas as pd
from datetime import datetime
from components.supabase_logic import supabase
from config import APP_SETTINGS

def show_profit_loss():
    st.title("📈 Profit & Loss Report")

    # 1. Date Selection UI
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Start Date", value=datetime.now().date())
    end_date = col_b.date_input("End Date", value=datetime.now().date())

    # 2. Supabase မှ တိုက်ရိုက် Data ဆွဲထုတ်ခြင်း (database.py ကို မသုံးတော့ပါ)
    try:
        sales_resp = supabase.table("sales").select("*").execute()
        sales_data = sales_resp.data or []
        
        products_resp = supabase.table("products").select("*").execute()
        products_data = products_resp.data or []
        product_map = {str(p.get('barcode')): p for p in products_data}
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    if not sales_data:
        st.info("Database ထဲတွင် အရောင်းမှတ်တမ်း မရှိသေးပါ။")
        return

    # 3. Processing and Filtering
    total_sales = 0
    total_cost = 0
    filtered_sales = []

    for sale in sales_data:
        # created_at က string ဖြစ်ရင် datetime ပြောင်းခြင်း
        raw_date = pd.to_datetime(sale.get('created_at'))
        sale_date = raw_date.date()

        # ရက်စွဲစစ်ခြင်း
        if start_date <= sale_date <= end_date:
            try:
                items_data = json.loads(sale.get('item', '[]'))
                totals_data = json.loads(sale.get('totals', '{}'))
                
                grand_total = float(totals_data.get("grand_total", 0))
                total_sales += grand_total
                
                # Cost တွက်ခြင်း
                for item in items_data:
                    barcode = str(item.get('barcode'))
                    qty = int(item.get('qty', 1))
                    prod = product_map.get(barcode, {})
                    buy_price = float(prod.get('cost_price', 0)) # cost_price ကို သုံးပါ
                    total_cost += (buy_price * qty)
                
                filtered_sales.append({
                    "ပြေစာအမှတ်": sale.get('receipt_no'),
                    "ရက်စွဲ": raw_date.strftime('%Y-%m-%d %H:%M'),
                    "စုစုပေါင်း (MMK)": grand_total,
                    "ပေးချေမှု": totals_data.get("payment_type", "Cash")
                })
            except Exception:
                continue

    # 4. Display Metrics
    net_profit = total_sales - total_cost
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 ရောင်းရငွေ (Sales)", f"{total_sales:,.0f} {APP_SETTINGS.get('currency', 'MMK')}")
    col2.metric("📉 ကုန်ကျစရိတ် (Cost)", f"{total_cost:,.0f} {APP_SETTINGS.get('currency', 'MMK')}")
    col3.metric("📊 အမြတ် (Profit)", f"{net_profit:,.0f} {APP_SETTINGS.get('currency', 'MMK')}")

    st.markdown("---")
    st.write("### 📝 အရောင်းမှတ်တမ်းအသေးစိတ်")
    
    if filtered_sales:
        df = pd.DataFrame(filtered_sales)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"ရွေးချယ်ထားသော {start_date} မှ {end_date} အတွင်း အရောင်းမှတ်တမ်း မတွေ့ရှိပါ။")
