import streamlit as st
import uuid  # <--- ဒီစာကြောင်းလေး ထည့်ပေးပါ
from datetime import datetime
from database import save_sale
from utils import show_receipt
from products import get_products_cached
from cart import add_to_cart, remove_from_cart, calculate_total

# အရေးကြီးဆုံးပြင်ဆင်ချက် - components လမ်းကြောင်းကို အပြည့်အစုံထည့်ပါ
# components/pos_system.py ရဲ့ အပေါ်ဆုံးမှာ
from components import supabase_logic
# ==========================================
# 1. Helper Functions
# ==========================================
def _get_product_price(product):
    return float(product.get('sell_price') or product.get('price') or 0)

def _generate_receipt_no():
    """Unique Receipt နံပါတ်ထုတ်ပေးခြင်း"""
    return "INV-" + uuid.uuid4().hex[:6].upper()
    """Database ကို လှမ်းမခေါ်ဘဲ Local မှာ Unique ID ထုတ်ပေးခြင်း (Lightning Fast)"""
    today_str = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"INV-{today_str}-{unique_id}"

def _process_checkout(cart, totals, payment_method, customer_name):
    """Checkout လုပ်ငန်းစဉ် (Offline-First နည်းလမ်း)"""
    rec_no = _generate_receipt_no()
    customer = customer_name if customer_name else "Walk-in"
    
    try:
        # 1. Local SQLite တွင် အရင်သိမ်းခြင်း (ချက်ချင်းပြီးဆုံး)
        save_sale(cart, totals, receipt_no=rec_no, payment_method=payment_method, customer_name=customer)
        
        # 2. Stock နုတ်ခြင်း (Local)
        process_sale_stock_update(cart)
        
        # 3. Supabase သို့ ပို့ရန် Pending List ထဲသို့ ထည့်ခြင်း
        if "pending_sales" not in st.session_state:
            st.session_state.pending_sales = []
        
        st.session_state.pending_sales.append({
            "cart": cart, "totals": totals, "rec_no": rec_no, 
            "payment_method": payment_method, "customer": customer
        })
        
        return rec_no, customer
    except Exception as e:
        st.error(f"⚠️ အရောင်းမှတ်တမ်း သိမ်းဆည်းရာတွင် အမှားအယွင်းရှိသည်: {e}")
        return None, None

# ==========================================
# 2. Main Run Module (POS UI)
# ==========================================
def show_pos_system():
    st.title("💰 POS System")

    # Sync ခလုတ် (အင်တာနက်ကောင်းမှ နှိပ်ပါ)
    if "pending_sales" in st.session_state and st.session_state.pending_sales:
        st.warning(f"⚠️ Sync မလုပ်ရသေးသော အရောင်း ( {len(st.session_state.pending_sales)} ) ခု ရှိသည်။")
        if st.button("🔄 Sync with Cloud"):
            with st.spinner("Sync လုပ်နေသည်..."):
                for sale in list(st.session_state.pending_sales):
                    try:
                        insert_sale_to_supabase(sale['cart'], sale['totals'], sale['rec_no'], sale['payment_method'], sale['customer'])
                        st.session_state.pending_sales.remove(sale)
                    except:
                        st.error("Sync လုပ်ရန် အင်တာနက် မရပါ။")
                        break
                st.rerun()

    # Receipt ပြသရန်
    if st.session_state.get("receipt"):
        show_receipt(st.session_state.receipt, st.session_state.receipt_totals, 
                     st.session_state.receipt_no, st.session_state.get("current_payment_method", "Cash"),
                     st.session_state.get("current_customer", "Walk-in"))
        if st.button("🖨️ နောက်တစ်ယောက် (Close Receipt)"):
            st.session_state.update({"receipt": None})
            st.rerun()
        st.markdown("---")

    products = get_products_cached()
    if products:
        product_map = {str(r.get('barcode')): r for r in products}
        product_options = {f"{r['product_name']} | ဈေး: {_get_product_price(r):,.0f} | {r.get('barcode')}": r for r in products}

        # Scan & Search
        st.text_input("🔫 Barcode Scan:", key="barcode_input", on_change=lambda: [
            st.session_state.update(cart=add_to_cart(st.session_state.cart, product_map[str(st.session_state.barcode_input)])),
            st.session_state.update(barcode_input="")
        ] if str(st.session_state.barcode_input) in product_map else None)

        st.selectbox("🔍 ပစ္စည်းရှာရန်:", [""] + list(product_options.keys()), key="prod_select", 
                     on_change=lambda: st.session_state.update(cart=add_to_cart(st.session_state.cart, product_options[st.session_state.prod_select])) if st.session_state.prod_select else None)

        # Cart Items
        if st.session_state.cart:
            for i, item in enumerate(st.session_state.cart):
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"{item.get('product_name')} ({_get_product_price(item):,.0f})")
                item['qty'] = col2.number_input("Qty", value=int(item.get('qty', 1)), min_value=1, key=f"q_{i}")
                if col3.button("❌", key=f"del_{i}"):
                    st.session_state.update(cart=remove_from_cart(st.session_state.cart, i))
                    st.rerun()

            st.markdown("---")
            tax_rate = st.number_input("Tax Rate (%)", value=0.0, step=0.1, format="%.1f") / 100
            discount = st.number_input("Discount (MMK)", value=0, step=100)
            totals = calculate_total(st.session_state.cart, tax_rate=tax_rate, discount=discount)
            st.subheader(f"Grand Total: {totals['grand_total']:,.0f} MMK")
            
            # Checkout
            payment_method = st.selectbox("💳 ငွေပေးချေမှုပုံစံ:", ["Cash", "Credit (အကြွေး)", "Installment (အရစ်ကျ)"], key="pay_method")
            customer_name = st.text_input("👤 ဖောက်သည်အမည်:", key="cust_name")
            
            if st.button("✅ Confirm Checkout"):
                if ("Credit" in payment_method or "Installment" in payment_method) and not customer_name:
                    st.warning("⚠️ ဖောက်သည်အမည် ထည့်ပေးရန် လိုအပ်ပါသည်။")
                else:
                    rec_no, customer = _process_checkout(st.session_state.cart, totals, payment_method, customer_name)
                    if rec_no:
                        st.session_state.update(receipt=st.session_state.cart, receipt_totals=totals, receipt_no=rec_no, 
                                                current_payment_method=payment_method, current_customer=customer, cart=[])
                        st.rerun()
