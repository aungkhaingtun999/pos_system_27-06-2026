import streamlit as st
import json
# တိုက်ရိုက် import လုပ်မည့်အစား အပေါ်တွင် သေချာစစ်ဆေးပါ
try:
    from components.supabase_logic import supabase, execute_refund
except ImportError:
    # အကယ်၍ package မတွေ့ပါက path ထည့်ပေးခြင်း
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from components.supabase_logic import supabase, execute_refund

def execute_refund(inv, items_to_refund):
    """
    Refund လုပ်ဆောင်ချက် - အဆင့်ဆင့် (Atomic Operation)
    """
    if not supabase: return 0
    
    # [Step 1: Strict Check] Database မှ နောက်ဆုံး status ကို တိုက်ရိုက်စစ်ပါ
    latest_check = supabase.table("sales").select("status").eq("id", inv['id']).single().execute().data
    
    if latest_check and latest_check.get("status") == "refunded":
        raise Exception("⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်၍ ထပ်မံလုပ်ဆောင်၍ မရပါ။")

    # [Step 2: Atomic Lock] လုပ်ငန်းစဉ် မစခင် Status ကို ချက်ချင်း 'refunded' ပြောင်းပါ
    # ဒီနေရာမှာ Database ကို ချက်ချင်း update လုပ်လိုက်တဲ့အတွက် အခြား request များ ဝင်မလာနိုင်တော့ပါ
    supabase.table("sales").update({"status": "refunded"}).eq("id", inv['id']).execute()

    try:
        total_refunded = 0
        # [Step 3: Stock Management]
        for item in items_to_refund:
            barcode = str(item.get('barcode'))
            qty = int(item.get('qty', 0))
            
            # Stock ပြန်တိုးခြင်း
            product = supabase.table("products").select("stock_qty").eq("barcode", barcode).single().execute().data
            if product:
                new_stock = int(product.get("stock_qty", 0)) + qty
                supabase.table("products").update({"stock_qty": new_stock}).eq("barcode", barcode).execute()
            
            price = float(item.get('sell_price') or item.get('price') or 0)
            total_refunded += (price * qty)
        
        # [Step 4: Logging]
        refund_data = {
            "receipt_no": inv.get('receipt_no'),
            "items": json.dumps(items_to_refund, ensure_ascii=False),
            "refund_amount": float(total_refunded),
            "refunded_at": datetime.now(pytz.timezone('Asia/Yangon')).isoformat()
        }
        supabase.table("refunds").insert(refund_data).execute()
        
        return total_refunded

    except Exception as e:
        # Error တက်ခဲ့လျှင် Refund အဖြစ် ပြန်မပြင်တော့ဘဲ error ပြပါ (Status က refunded ဖြစ်နေမှာပဲ)
        raise Exception(f"Refund လုပ်ဆောင်ရာတွင် အမှားဖြစ်ပွားသည်: {e}")
