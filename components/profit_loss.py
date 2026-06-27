# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
import json
import pandas as pd
from database import get_sales
from products import get_products_cached
from config import APP_SETTINGS

# ==========================================
# 2. Helper Functions (Advanced Calculation)
# ==========================================
def _calculate_detailed_profit(sales, products):
    total_sales = 0
    total_cost = 0
    product_map = {str(p.get('barcode')): p for p in products}
    
    for sale in sales:
        # sale variable သည် tuple ဖြစ်သည်
        # sales table schema: (id, receipt_no, sale_date, items, totals, ...)
        items_json = sale[3]  # Items
        totals_json = sale[4] # Totals
        
        try:
            # JSON string ကို Dictionary သို့ ပြောင်းခြင်း
            items_data = json.loads(items_json) if isinstance(items_json, str) else items_json
            totals_data = json.loads(totals_json) if isinstance(totals_json, str) else totals_json
            
            # totals_data က list ဖြစ်နေရင် ပထမဆုံး item ကို ယူရန်
            if isinstance(totals_data, list): 
                totals_data = totals_data[0]
            
            # Grand Total တွက်ခြင်း
            total_sales += float(totals_data.get("grand_total", 0))
            
            # Cost တွက်ခြင်း
            for item in items_data:
                barcode = str(item.get('barcode'))
                qty = int(item.get('qty', 1))
                prod = product_map.get(barcode, {})
                buy_price = float(prod.get('buy_price', 0))
                total_cost += (buy_price * qty)
        except Exception as e:
            continue
            
    return {
        "total_sales": total_sales,
        "total_cost": total_cost,
        "net_profit": total_sales - total_cost
    }

# ==========================================
# 3. Main Run Module (Profit & Loss UI)
# ==========================================
def show_profit_loss():
    """Profit & Loss Dashboard ကို render လုပ်ပေးခြင်း"""
    st.title("📈 Profit & Loss Report")

    # Data Fetching
    sales = get_sales()
    products = get_products_cached()
    
    if not sales:
        st.info("လက်ရှိတွင် အရောင်းမှတ်တမ်း မရှိသေးပါ။")
        return

    # Calculations
    data = _calculate_detailed_profit(sales, products)

    # Display Metrics
    col1, col2, col3 = st.columns(3)
    
    col1.metric("💰 ရောင်းရငွေ (Sales)", f"{data['total_sales']:,.0f} {APP_SETTINGS['currency']}")
    col2.metric("📉 ကုန်ကျစရိတ် (Cost)", f"{data['total_cost']:,.0f} {APP_SETTINGS['currency']}")
    col3.metric("📊 အမြတ် (Profit)", f"{data['net_profit']:,.0f} {APP_SETTINGS['currency']}", delta_color="normal")

    st.markdown("---")
    st.write("### 📝 အရောင်းမှတ်တမ်းအသေးစိတ်")
    
    # ပြေစာစာရင်းကို လှပသော Table ပုံစံပြသရန်
    formatted_sales = []
    for sale in sales:
        try:
            totals = json.loads(sale[4]) if isinstance(sale[4], str) else sale[4]
            formatted_sales.append({
                "ပြေစာအမှတ်": sale[1],
                "ရက်စွဲ": sale[2],
                "စုစုပေါင်း (MMK)": float(totals.get("grand_total", 0)),
                "ပေးချေမှု": totals.get("payment_method", "Cash")
            })
        except:
            continue
    
    if formatted_sales:
        df = pd.DataFrame(formatted_sales)
        st.dataframe(
            df, 
            column_config={
                "စုစုပေါင်း (MMK)": st.column_config.NumberColumn("စုစုပေါင်း (MMK)", format="%.0f"),
            },
            use_container_width=True
        )