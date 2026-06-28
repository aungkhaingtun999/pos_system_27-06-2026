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
# 2. Sale Functions
# ==========================================
def insert_sale(cart, totals, receipt_no, payment_method, customer_name):
    if not supabase: raise Exception("Database Connection မရှိပါ။")
    data = {
        "receipt_no": receipt_no,
        "customer_name": customer_name,
        "grand_total": float(totals.get("grand_total", 0)),
        "payment_type": payment_method,
        "created_at": get_myanmar_time().isoformat(),
        "item": json.dumps(cart, ensure_ascii=False),
        "totals": json.dumps(totals, ensure_ascii=False),
        "status": "active" 
    }
    return supabase.table("sales").insert(data).execute()

def process_sale_stock_update(cart):
    if not supabase: return
    for item in cart:
        barcode = str(item.get("barcode"))
        qty = int(item.get("qty", 0))
        product = supabase.table("products").select("stock_qty").eq("barcode", barcode).single().execute().data
        if product:
            new_stock = int(product.get("stock_qty", 0)) - qty
            supabase.table("products").update({"stock_qty": new_stock}).eq("barcode", barcode).execute()

# ==========================================
# 3. Optimized Refund Function (Fixed)
# ==========================================
def execute_refund(inv, items_to_refund):
    """
    Refund လုပ်ဆောင်ချက်-
    1. [Atomic Check] Status အရင်စစ်
    2. [Locking] Status ကို 'refunded' ချက်ချင်းပြောင်း (အကြိမ်ကြိမ်လုပ်၍မရအောင်)
    3. Stock ပြန်တိုး
    4. Refund Log သွင်း
    """
    if not supabase: return 0
    
    # [Step 1]: Database မှ လက်ရှိ status ကို နောက်ဆုံးတစ်ကြိမ် တိုက်ရိုက်စစ်ပါ
    latest_check = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
    if latest_check and latest_check.get("status") == "refunded":
        raise Exception("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")

    # [Step 2 - CRITICAL]: Refund မစခင် status ကို 'refunded' အရင်ပြောင်းထားပါ (Locking)
    # ဤအဆင့်က အခြား process များမှ ထပ်မံ Refund လုပ်ခြင်းကို တားဆီးပေးမည်
    supabase.table("sales").update({"status": "refunded"}).eq("id", inv['id']).execute()

    try:
        total_refunded = 0
        # [Step 3]: Stock ပြန်တိုးခြင်း
        for item in items_to_refund:
            barcode = str(item.get('barcode'))
            qty = int(item.get('qty', 0))
            
            product = supabase.table("products").select("stock_qty").eq("barcode", barcode).single().execute().data
            if product:
                new_stock = int(product.get("stock_qty", 0)) + qty
                supabase.table("products").update({"stock_qty": new_stock}).eq("barcode", barcode).execute()
                
            price = float(item.get('sell_price') or item.get('price') or 0)
            total_refunded += (price * qty)
        
        # [Step 4]: Refund Log သိမ်းခြင်း
        refund_data = {
            "receipt_no": inv.get('receipt_no'),
            "items": json.dumps(items_to_refund, ensure_ascii=False),
            "refund_amount": float(total_refunded),
            "refunded_at": get_myanmar_time().isoformat(),
            "details": f"Refunded {len(items_to_refund)} items"
        }
        supabase.table("refunds").insert(refund_data).execute()
        
        return total_refunded

    except Exception as e:
        # အကယ်၍ အမှားတစ်ခုခုဖြစ်ခဲ့လျှင် status ကို ပြန်ဖွင့်ပေးရန် လိုအပ်ပါက ဤနေရာတွင် logic ထည့်ပါ
        # သို့သော် များသောအားဖြင့် status ကို 'refunded' အဖြစ်ထားခဲ့ခြင်းက ပို၍လုံခြုံသည်
        raise Exception(f"Refund လုပ်ဆောင်စဉ် အမှားဖြစ်ပွားသည်: {e}")
