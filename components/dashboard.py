# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
from database import get_sales
from utils import format_currency

# ==========================================
# 2. Helper Functions (Data Calculation)
# ==========================================
def _get_dashboard_metrics(sales):
    """Sales Data မှ Metric များကို တွက်ချက်ခြင်း"""
    total_sales = sum(s["grand_total"] for s in sales)
    total_orders = len(sales)
    return total_sales, total_orders

# ==========================================
# 3. Main Run Module (Dashboard UI)
# ==========================================
def show_dashboard():
    """Dashboard UI ကို render လုပ်ပေးသော Main module"""
    st.title("📊 Daily Dashboard")

    # Data Fetching
    sales = get_sales()
    
    # Calculations
    total_sales, total_orders = _get_dashboard_metrics(sales)

    # Display Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sales", format_currency(total_sales))
    with col2:
        st.metric("Orders", total_orders)

    # Display Recent Sales
    st.write("### 📝 Recent Sales")
    if not sales.empty:
        st.dataframe(sales, use_container_width=True)
    else:
        st.info("လက်ရှိတွင် ရောင်းချထားမှု မရှိသေးပါ။")

# ==========================================
# Note on Unicode (UTF-8)
# ==========================================
# ဤဖိုင်သည် UTF-8 encoding ဖြင့် သိမ်းဆည်းရန်အတွက် အဆင်သင့်ဖြစ်နေပါသည်။
# မြန်မာစာ Unicode များ အဆင်ပြေစေရန်အတွက် system ၏ font setting များကို 
# ဂရုစိုက်ရန်လိုအပ်ပါသည်။