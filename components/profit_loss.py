import streamlit as st
import json
import pandas as pd
from datetime import datetime
from components.supabase_logic import supabase

def show_profit_loss():
    st.title("📈 Profit & Loss Report")

    # Date Range Selection
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Start Date", value=datetime.now().date())
    end_date = col_b.date_input("End Date", value=datetime.now().date())

    try:
        # Fetching Data
        sales_data = supabase.table("sales").select("*").execute().data or []
        products_data = supabase.table("products").select("*").execute().data or []
        # 3.png အရ column နာမည်များအတိုင်း သုံးထားသည်
        expenses_data = supabase.table("expenses").select("*").execute().data or []
        
        product_map = {str(p.get('barcode')): p for p in products_data}
    except Exception as e:
        st.error(f"Database Error: {e}")
        return

    # 1. Variables initialization
    total_sales = 0
    total_cogs = 0 
    total_tax = 0
    total_discount = 0
    total_expenses = 0
    filtered_sales = []

    # 2. Sales Processing
    for sale in sales_data:
        # created_at ရှိမရှိစစ်ဆေးခြင်း
        if not sale.get('created_at'): continue
        
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
                    # 4.png အရ sell_price ကို သုံးပါ
                    buy_price = float(prod.get('cost_price') or prod.get('buy_price') or 0)
                    total_cogs += (buy_price * int(item.get('qty', 1)))
                
                filtered_sales.append({"Receipt": sale.get('receipt_no'), "Total": grand_total})
            except: continue

    # 3. Expenses Processing
    for ex in expenses_data:
        # 3.png အရ expense_date column ကိုသုံးပါ
        if ex.get('expense_date'):
            ex_date = pd.to_datetime(ex.get('expense_date')).date()
            if start_date <= ex_date <= end_date:
                total_expenses += float(ex.get('amount', 0))

    # 4. Net Profit Calculation
    net_profit = total_sales - total_cogs - total_expenses - total_discount - total_tax

    # Formatting helper
    def fmt(val):
        return f"{val:,.2f}"

    # 5. Display Metrics
    st.subheader(f"📊 Summary ({start_date} to {end_date})")
    c1, c2 = st.columns(2)
    c1.metric("💰 စုစုပေါင်းရောင်းရငွေ", fmt(total_sales))
    c2.metric("🎯 အသားတင်အမြတ်", fmt(net_profit))
    
    st.write("---")
    sub_c1, sub_c2, sub_c3, sub_c4 = st.columns(4)
    sub_c1.metric("📉 ကုန်ပစ္စည်းဝယ်ဈေး", fmt(total_cogs))
    sub_c2.metric("🛠️ လည်ပတ်မှုစရိတ်", fmt(total_expenses))
    sub_c3.metric("🏷️ Discount", fmt(total_discount))
    sub_c4.metric("⚖️ Tax", fmt(total_tax))

    st.write("---")
    
    # 6. Detailed Table
    if filtered_sales:
        st.write("### 📝 အရောင်းမှတ်တမ်းအသေးစိတ်")
        df = pd.DataFrame(filtered_sales)
        st.dataframe(
            df.style.format({"Total": "{:,.2f}"}), 
            use_container_width=True
        )
    else:
        st.info("ရွေးချယ်ထားသော ရက်စွဲများအတွင်း အရောင်းမှတ်တမ်း မရှိပါ။")
