# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
from database import get_sales
from utils import money

# ==========================================
# 2. Helper Functions (Data Calculation)
# ==========================================
def _calculate_dashboard_metrics(sales):
    """Sales data မှ အဓိက metrics များကို တွက်ချက်ပေးခြင်း"""
    total_sales = sum(s["grand_total"] for s in sales)
    order_count = len(sales)
    return {
        "total": total_sales,
        "count": order_count
    }

# ==========================================
# 3. Run Module (UI Component)
# ==========================================
def show_dashboard():
    """Dashboard UI ကို render လုပ်ပေးသော Main module"""
    st.title("📊 Daily Dashboard")

    # Data Fetching
    sales = get_sales()
    metrics = _calculate_dashboard_metrics(sales)

    # Display Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sales", money(metrics["total"]))
    with col2:
        st.metric("Orders", metrics["count"])

    # Display Details
    st.write("### Recent Sales")
    if sales:
        st.dataframe(sales, use_container_width=True)
    else:
        st.info("လက်ရှိတွင် ရောင်းချထားမှု မရှိသေးပါ။")

# ==========================================
# Note on Unicode (UTF-8)
# ==========================================
# Dashboard တွင် မြန်မာစာ (Unicode) များ အသုံးပြုထားသော်လည်း 
# Streamlit က UTF-8 ကို default အနေဖြင့် အလိုအလျောက် ပံ့ပိုးပေးပါသည်။
# Report သို့မဟုတ် File အနေဖြင့် Export ထုတ်လိုပါက 
# encoding="utf-8" ကို သုံး၍ သိမ်းဆည်းရန် မမေ့ပါနှင့်။