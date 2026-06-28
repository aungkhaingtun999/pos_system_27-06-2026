import streamlit as st
import json
from supabase import create_client
from datetime import datetime
import pytz

# Supabase Client
@st.cache_resource
def _get_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    return create_client(url, key) if url and key else None

supabase = _get_client()

def sync_to_supabase(pending_sales):
    """Sync logic: pending_sales (list) ကို အတိအကျ လက်ခံသည်"""
    if not supabase: raise Exception("Database Connection မရှိပါ။")
    for sale in pending_sales:
        # insert_sale function ကို ခေါ်ခြင်း
        data = {
            "receipt_no": sale['rec_no'],
            "customer_name": sale['customer'],
            "grand_total": float(sale['totals'].get("grand_total", 0)),
            "payment_type": sale['payment_method'],
            "created_at": datetime.now(pytz.timezone('Asia/Yangon')).isoformat(),
            "item": json.dumps(sale['cart'], ensure_ascii=False),
            "totals": json.dumps(sale['totals'], ensure_ascii=False),
            "status": "active"
        }
        supabase.table("sales").insert(data).execute()

def execute_refund(inv, items_to_refund):
    """Refund Logic: Double Check ဖြင့် Refund လုပ်သည်"""
    if not supabase: return 0
    
    # 1. DB မှ နောက်ဆုံး status ကို စစ်ခြင်း
    check = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
    if check and check.get("status") == "refunded":
        raise Exception("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")

    # 2. Status update လုပ်ခြင်း
    supabase.table("sales").update({"status": "refunded"}).eq("id", inv['id']).execute()
    
    total_refunded = sum([float(item.get('price', 0)) * int(item.get('qty', 1)) for item in items_to_refund])
    
    # 3. Refund table သို့ ထည့်ခြင်း
    refund_data = {
        "receipt_no": inv.get('receipt_no'),
        "items": json.dumps(items_to_refund, ensure_ascii=False),
        "refund_amount": float(total_refunded),
        "refunded_at": datetime.now(pytz.timezone('Asia/Yangon')).isoformat(),
        "status": "completed",
        "details": f"Refunded {len(items_to_refund)} items"
    }
    supabase.table("refunds").insert(refund_data).execute()
    return total_refunded
