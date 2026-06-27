# ==========================================
# 1. Imports
# ==========================================
import streamlit as st
import pandas as pd
from database import get_products
from cart_utils import add_to_cart, remove_from_cart, calculate_total
from config import init_session

# ==========================================
# 2. Helper Functions (Business Logic)
# ==========================================
def find_product_by_barcode(products, barcode):
    """Barcode ဖြင့် ပစ္စည်းရှာခြင်း"""
    for p in products:
        if str(p.get("barcode", "")).strip() == barcode:
            return p
    return None

def save_checkout_data(data):
    """Checkout data ကို Unicode (UTF-8) ဖြင့် သိမ်းဆည်းခြင်း"""
    import json
    with open("checkout_log.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 3. Main Run Module (UI Components)
# ==========================================
def main():
    st.set_page_config(page_title="Barcode POS", layout="wide")
    init_session()
    
    st.title("💰 Barcode POS System")
    products = get_products()

    # --- Barcode Scanner Section ---
    st.subheader("📷 Scan Barcode")
    barcode_input = st.text_input("Barcode", placeholder="Scan here...")
    if barcode_input:
        product = find_product_by_barcode(products, barcode_input.strip())
        if product:
            st.session_state.cart = add_to_cart(st.session_state.cart, product)
            st.success(f"{product['product_name']} Added")
            st.rerun()
        else:
            st.error("Barcode မတွေ့ပါ")

    # --- Manual Search ---
    st.divider()
    st.subheader("🔍 Manual Search")
    search = st.text_input("Product Name")
    if search:
        results = [p for p in products if search.lower() in p["product_name"].lower()]
        for p in results:
            col1, col2, col3 = st.columns(3)
            col1.write(p["product_name"])
            col2.write(f"{p['sell_price']} MMK")
            if col3.button("Add", key=f"add_{p['id']}"):
                st.session_state.cart = add_to_cart(st.session_state.cart, p)
                st.rerun()

    # --- Cart Section ---
    st.divider()
    st.subheader("🛒 CART")
    if not st.session_state.cart:
        st.info("Cart Empty")
    else:
        for index, item in enumerate(st.session_state.cart):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            col1.write(item["product_name"])
            col2.write(f"{item['sell_price']} MMK")
            
            if col3.button("+", key=f"plus_{index}"):
                item["qty"] += 1
                st.rerun()
            
            col4.write(item["qty"])
            
            if col5.button("-", key=f"minus_{index}"):
                if item["qty"] > 1:
                    item["qty"] -= 1
                else:
                    st.session_state.cart = remove_from_cart(st.session_state.cart, index)
                st.rerun()

        # --- Checkout Calculations ---
        discount = st.number_input("Discount (%)", min_value=0.0, value=0.0)
        tax = st.number_input("Tax (%)", min_value=0.0, value=0.0)
        
        totals = calculate_total(st.session_state.cart, tax_rate=tax/100, discount=(sum(i['sell_price']*i['qty'] for i in st.session_state.cart) * discount/100))
        
        st.success(f"TOTAL : {totals['grand_total']} MMK")

        if st.button("🔴 CHECKOUT"):
            checkout_data = {"cart": st.session_state.cart, **totals}
            save_checkout_data(checkout_data) # Unicode သိမ်းခြင်း
            st.success("Checkout Data Saved (UTF-8)")
            st.json(checkout_data)

if __name__ == "__main__":
    main()