# ==========================================
# 1. Imports
# ==========================================
import streamlit as st

# ==========================================
# 2. Helper Functions (Data Processing)
# ==========================================
def _validate_product_data(product):
    """ပစ္စည်းတစ်ခုတွင် လိုအပ်သော data များ ရှိမရှိ စစ်ဆေးပြီး ပုံစံထုတ်ပေးခြင်း"""
    if "barcode" not in product:
        return None
    
    # လိုအပ်သော defaults များ သတ်မှတ်ခြင်း
    processed_item = product.copy()
    processed_item.setdefault("buy_price", 0)
    processed_item.setdefault("sell_price", 0)
    processed_item.setdefault("product_name", "Unknown")
    processed_item.setdefault("qty", 1)
    
    return processed_item

# ==========================================
# 3. Main Modules (Cart Business Logic)
# ==========================================
def add_to_cart(cart, product):
    """Cart ထဲသို့ ပစ္စည်းထည့်ခြင်း (Barcode ကို အခြေခံသည်)"""
    barcode = str(product.get("barcode", ""))
    if not barcode:
        st.error("Error: Product missing barcode!")
        return cart

    # ပစ္စည်းတူ/မတူ စစ်ဆေးခြင်း (တူပါက အရေအတွက် တိုးမည်)
    for item in cart:
        if str(item.get("barcode")) == barcode:
            item["qty"] = item.get("qty", 0) + 1
            return cart
    
    # ပစ္စည်းအသစ်ဖြစ်လျှင် Cart ထဲ ထည့်ခြင်း
    new_item = _validate_product_data(product)
    if new_item:
        cart.append(new_item)
        
    return cart

def remove_from_cart(cart, index):
    """Cart ထဲမှ ပစ္စည်းဖယ်ရှားခြင်း"""
    if 0 <= index < len(cart): 
        cart.pop(index)
    return cart

def calculate_total(cart, tax_rate=0, discount=0):
    """Total တွက်ချက်ခြင်း"""
    subtotal = sum(float(item.get("sell_price", 0)) * float(item.get("qty", 0)) for item in cart)
    
    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount - discount
    
    return {
        "subtotal": subtotal,
        "tax": tax_amount,
        "discount": discount,
        "grand_total": max(0, grand_total)
    }

def update_stock_locally(cart):
    """
    (Optional) UI ပေါ်တွင် လက်ကျန်ကို ချက်ချင်း update ဖြစ်စေရန်
    နောက်ဆုံးအဆင့် Save လုပ်တဲ့အခါ Database ကနေ တိုက်ရိုက်နုတ်တာ ပိုကောင်းပါတယ်
    """
    pass