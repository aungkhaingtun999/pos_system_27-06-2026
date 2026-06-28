import streamlit as st
import json
from supabase import create_client
from datetime import datetime
import pytz

# ==========================================
# 0. Helper Functions
# ==========================================
def get_myanmar_time():
    myanmar_tz = pytz.timezone('Asia/Yangon')
    return datetime.now(myanmar_tz)

# ==========================================
# 1. Connection Initialization
# ==========================================
@st.cache_resource
def _get_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

supabase = _get_client()

# ==========================================
# 2. Refund Function (Strict & Clean)
# ==========================================
def execute_refund(inv, items_to_refund):
    """
    Refund လုပ်ဆောင်ချက်-
    1. Status အရင်စစ် (Double-check)
    2. Stock ပြန်တိုး
    3. Refund Log သွင်း
    4. Sale Status ပြောင်း
    """
    if not supabase: return 0
    
    # [Step 1] အရေးကြီး: Refund လုပ်ပြီးသားဖြစ်မဖြစ် နောက်ဆုံးတစ်ကြိမ် ပြန်စစ်ပါ
    check = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
    if check and check.get("status") == "refunded":
        raise Exception("ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")

    total_refunded = 0
    
    # [Step 2] Stock ပြန်တိုးခြင်း
    for item in items_to_refund:
        barcode = str(item.get('barcode'))
        qty = int(item.get('qty', 0))
        
        # Product ကို Database မှ အသစ်ပြန်ခေါ် (Cache မသုံးပါ)
        product = supabase.table("products").select("stock_qty").eq("barcode", barcode).single().execute().data
        if product:
            new_stock = int(product.get("stock_qty", 0)) + qty
            supabase.table("products").update({"stock_qty": new_stock}).eq("barcode", barcode).execute()
            
        price = float(item.get('sell_price') or item.get('price') or 0)
        total_refunded += (price * qty)
    
    # [Step 3] Refund Log သိမ်းခြင်း
    refund_data = {
        "receipt_no": inv.get('receipt_no'),
        "items": json.dumps(items_to_refund, ensure_ascii=False),
        "refund_amount": float(total_refunded),
        "refunded_at": get_myanmar_time().isoformat(),
        "details": f"Refunded {len(items_to_refund)} items"
    }
    supabase.table("refunds").insert(refund_data).execute()
    
    # [Step 4] Sales Receipt ကို 'refunded' ဟု အမှတ်အသားပြုခြင်း
    supabase.table("sales").update({"status": "refunded"}).eq("id", inv['id']).execute()
    
    return total_refunded
