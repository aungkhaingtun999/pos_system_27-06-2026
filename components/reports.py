import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database import get_report_by_date
from components.supabase_logic import supabase

# ==========================================
# 2. Helper Functions (Data Processing)
# ==========================================
def _process_report_data(report_data, refund_data, start_date, end_date):
    summary = []
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    data_list = report_data
    if isinstance(data_list, list):
        for sale in data_list:
            if isinstance(sale, (list, tuple)) and len(sale) >= 5:
                try:
                    raw_date = pd.to_datetime(sale[2])
                    sale_date_str = raw_date.strftime('%Y-%m-%d')
                    
                    if start_str <= sale_date_str <= end_str:
                        raw_totals = sale[4]
                        totals = json.loads(raw_totals) if isinstance(raw_totals, str) else raw_totals
                        amount = float(totals.get("grand_total", totals.get("total", 0)))
                        
                        summary.append({
                            "Date": raw_date,
                            "Type": "Sale", 
                            "Amount": amount
                        })
                except Exception as e:
                    continue
    
    # Refund Logic
    for r in refund_data:
        try:
            refund_ts = pd.to_datetime(r.get("refunded_at"))
            refund_date_str = refund_ts.strftime('%Y-%m-%d')
            if start_str <= refund_date_str <= end_str:
                summary.append({
                    "Date": refund_ts, 
                    "Type": "Refund", 
                    "Amount": -float(r.get("refund_amount", 0))
                })
        except: continue
        
    return summary

def _format_dataframe(df, view_type):
    if df.empty: return pd.DataFrame(columns=['Sale', 'Refund', 'Net Total'])
    
    # ပြင်ဆင်ချက် - utc=True ကို ထည့်ပေးလိုက်ပါ
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    
    # နေ့/လ/နှစ် အလိုက် ပြောင်းလဲခြင်း (Timezone ကို ဖြုတ်ပြီးမှ နှိုင်းယှဉ်ပါ)
    # tz_localize(None) သည် Timezone ကို ဖြုတ်ပေးသည်
    if view_type == "လချုပ်": 
        df['Period'] = df['Date'].dt.tz_localize(None).dt.to_period('M')
    elif view_type == "နှစ်ချုပ်": 
        df['Period'] = df['Date'].dt.tz_localize(None).dt.to_period('Y')
    else: 
        df['Period'] = df['Date'].dt.tz_localize(None).dt.date
    
    final_df = df.groupby(['Period', 'Type'])['Amount'].sum().unstack(fill_value=0)
    
    if 'Sale' not in final_df.columns: final_df['Sale'] = 0.0
    if 'Refund' not in final_df.columns: final_df['Refund'] = 0.0
    
    final_df['Net Total'] = final_df['Sale'] + final_df['Refund']
    return final_df
# ==========================================
# 3. Main Run Module (Reports UI)
# ==========================================
def show_reports():
    st.title("📊 Sales & Refund Summary Report")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    start_date = col1.date_input("Start Date", value=datetime.now().date())
    end_date = col2.date_input("End Date", value=datetime.now().date())
    view_type = col3.selectbox("Report အမျိုးအစား:", ["ရက်ချုပ်", "လချုပ်", "နှစ်ချုပ်"])
    
    report = get_report_by_date(start_date, end_date)
    
    try:
        refunds = supabase.table("refunds").select("*").execute().data or []
    except: refunds = []
    
    summary_list = _process_report_data(report, refunds, start_date, end_date)
    
    if summary_list:
        final_df = _format_dataframe(pd.DataFrame(summary_list), view_type)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 ရောင်းရငွေ", f"{final_df['Sale'].sum():,.2f} MMK")
        c2.metric("🔄 Refund", f"{abs(final_df['Refund'].sum()):,.2f} MMK")
        c3.metric("🎯 အသားတင်ရငွေ", f"{final_df['Net Total'].sum():,.2f} MMK")
        
        st.dataframe(final_df.style.format("{:,.2f} MMK"), use_container_width=True)
        
        

# --- Reprint Receipt ---
        st.markdown("---")
        st.subheader("🧾 Reprint Receipt")
        
        # 1. Start/End date ကို string ပြန်ပြောင်းပြီး အတည်ပြုပါ
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        receipt_map = {}
        
        # 2. report (Database data) ကို တိုက်ရိုက် Loop ပတ်ပြီး စစ်ပါ
        # report ဆိုသည်မှာ get_report_by_date() မှရလာသော list ဖြစ်သည်
        if isinstance(report, list):
            for r in report:
                if isinstance(r, (list, tuple)) and len(r) > 4:
                    # ရက်စွဲကို string ပြောင်းပြီး နှိုင်းယှဉ်ပါ
                    try:
                        r_date = pd.to_datetime(r[2]).strftime('%Y-%m-%d')
                        if start_str <= r_date <= end_str:
                            # Receipt နံပါတ် နှင့် ရက်စွဲကို သော့အဖြစ်သုံးပါ
                            receipt_key = f"Receipt #{r[1]} ({r[2]})"
                            receipt_map[receipt_key] = r
                    except:
                        continue
        
        # 3. Display Logic
        if receipt_map:
            selected = st.selectbox("Receipt နံပါတ် ရွေးပါ:", list(receipt_map.keys()), key="reprint_sel")
            if st.button("🖨️ Print Receipt"):
                row = receipt_map[selected]
                items = json.loads(row[3]) if isinstance(row[3], str) else row[3]
                totals = json.loads(row[4]) if isinstance(row[4], str) else row[4]
                
                # Session State ရှင်းလင်းပြီးမှ အသစ်ထည့်ပါ
                st.session_state.receipt = items
                st.session_state.receipt_totals = totals
                st.session_state.receipt_no = row[1]
                st.session_state.menu = "POS System"
                st.session_state.is_reprint = True  # အရေးကြီးသည်
                st.rerun()
        else:
            st.info("ရွေးချယ်ထားသော ရက်စွဲတွင် Reprint ဆွဲရန် Receipt များ မရှိပါ။ (ရက်စွဲကို ပြန်စစ်ကြည့်ပါ)")