# ==========================================
# 1. Language Dictionary
# ==========================================
def get_language_data():
    """ဘာသာစကားဆိုင်ရာ စာသားများကို Dictionary အနေဖြင့် ပြန်ပေးခြင်း"""
    return {
        "EN": {
            "menu": ["POS System", "Reports", "Inventory", "Refund", "Profit & Loss"],
            "title": "Barcode POS System",
            "scanner": "Barcode Scanner",
            "scan_input": "Scan barcode here...",
            "search": "Product Search",
            "search_input": "Type product name...",
            "cart": "Current Cart",
            "checkout": "Checkout",
            "discount": "Discount %",
            "tax": "Tax %",
            "grand_total": "Grand Total",
            "confirm": "Confirm Sale",
            "empty_cart": "Cart is empty.",
            "Online": "✅ Online",
            "Offline": "❌ Offline"
        },
        "MY": {
            "menu": ["အရောင်းစနစ် (POS)", "မှတ်တမ်းများ", "ပစ္စည်းလက်ကျန်", "ပြန်အမ်းငွေ (Refund)", "အမြတ်/အရှုံး"],
            "title": "ဘားကုဒ် POS စနစ်",
            "scanner": "ဘားကုဒ် စကင်ဖတ်ရန်",
            "scan_input": "ဘားကုဒ်ကို စကင်ဖတ်ပါ...",
            "search": "ပစ္စည်း ရှာရန်",
            "search_input": "ပစ္စည်းအမည် ရိုက်ထည့်ပါ...",
            "cart": "ခြင်းတောင်း",
            "checkout": "ငွေရှင်းရန်",
            "discount": "လျှော့စျေး %",
            "tax": "အခွန် %",
            "grand_total": "စုစုပေါင်း ကျသင့်ငွေ",
            "confirm": "အရောင်း အတည်ပြုမည်",
            "empty_cart": "ခြင်းတောင်း လွတ်နေသည်။",
            "Online": "✅ အွန်လိုင်း",
            "Offline": "❌ အော့ဖ်လိုင်း"
        }
    }

# ==========================================
# 2. Main Getter Function
# ==========================================
def get_text(key, lang=None):
    """
    သတ်မှတ်ထားသော key နှင့် lang ကိုယူပြီး စာသားများ ပြန်ပေးခြင်း
    အသုံးပြုပုံ - text = get_text("Online", "MY")
    """
    if lang is None:
        import streamlit as st
        lang = st.session_state.get("lang", "MY")
        
    data = get_language_data()
    # ရွေးချယ်ထားသော ဘာသာစကားမရှိပါက MY ကို Default ပြန်ပေးမည်
    lang_data = data.get(lang, data["MY"])
    
    # သတ်မှတ်ထားသော key အတွက် စာသားပြန်ပေးခြင်း (key မရှိပါက key အတိုင်းပြန်ပေး)
    return lang_data.get(key, key)