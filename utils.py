import streamlit as st
from datetime import datetime

# ==========================================
# 2. Helper Functions (Receipt & Formatting)
# ==========================================
def _get_items_html(data):
    """Receipt အတွက် Items List ကို HTML format ပြောင်းပေးခြင်း"""
    items_html = ""
    for item in data:
        price = float(item.get('sell_price') or item.get('price', 0))
        qty = float(item.get('qty', 0))
        line_total = qty * price
        items_html += f"""
        <tr>
            <td style="padding: 2px; width: 40%; word-wrap: break-word;">{item.get('product_name', 'Item')}</td>
            <td style="text-align:center; padding: 2px; width: 10%;">{qty:.0f}</td>
            <td style="text-align:right; padding: 2px; width: 25%;">{price:,.2f}</td>
            <td style="text-align:right; padding: 2px; width: 25%;">{line_total:,.2f}</td>
        </tr>"""
    return items_html

def _get_receipt_html(data, totals, receipt_no, payment_method, customer):
    """PDF/Print Receipt အတွက် Template"""
    items_html = _get_items_html(data)
    # HTML Content ကို ပြင်ဆင်ခြင်း
    return f"""
    <div id="receipt-content" style="width: 320px; padding: 10px; font-family: 'Courier New', monospace; border: 1px solid #000;">
        <h3 style="text-align:center; margin: 0;">OFFICIAL RECEIPT</h3>
        <p style="text-align:center; font-size: 11px; margin: 5px 0;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p style="font-size: 11px; margin: 0;">No: {receipt_no}</p>
        <p style="font-size: 11px; margin: 0;">Customer: {customer}</p>
        <p style="font-size: 11px; margin: 0;">Method: {payment_method}</p>
        <hr style="border-top: 1px dashed #000;">
        <table style="width:100%; font-size: 11px; table-layout: fixed;">
            <tr><th style="text-align:left; width: 40%;">Item</th><th style="width: 10%;">Qty</th>
                <th style="text-align:right; width: 25%;">Price</th><th style="text-align:right; width: 25%;">Total</th></tr>
            {items_html}
        </table>
        <hr style="border-top: 1px dashed #000;">
        <div style="font-size: 12px;">
            <p style="text-align:right; margin: 2px 0;">Subtotal: {float(totals.get('subtotal', 0)):,.2f}</p>
            <p style="text-align:right; margin: 2px 0;">Tax: {float(totals.get('tax', 0)):,.2f}</p>
            <p style="text-align:right; margin: 2px 0;">Discount: {float(totals.get('discount', 0)):,.2f}</p>
            <p style="text-align:right; font-size: 14px; font-weight: bold; margin-top: 8px;">
                GRAND TOTAL: {float(totals.get('grand_total', 0)):,.2f} MMK</p>
        </div>
        <p style="text-align:center; font-size: 10px; margin-top: 10px;">*** Thank you! ***</p>
    </div>
    """

# ==========================================
# 3. Run Modules (UI Component & Utilities)
# ==========================================
def init_app_state():
    """Application State Initialize လုပ်ခြင်း"""
    if "cart" not in st.session_state: st.session_state.cart = []
    if "receipt" not in st.session_state: st.session_state.receipt = None
    if "show_pwd_change" not in st.session_state: st.session_state.show_pwd_change = False
    
    params = st.query_params
    if "menu" not in st.session_state:
        st.session_state.menu = params.get("menu", "POS System")

def show_receipt(data, totals, receipt_no, payment_method="Cash", customer="Walk-in"):
    """Receipt UI ကို ပြသခြင်းနှင့် Print လုပ်ဆောင်ခြင်း"""
    html_content = _get_receipt_html(data, totals, receipt_no, payment_method, customer)
    
    # Print function ပါဝင်သော HTML
    final_html = f"""
    {html_content}
    <script>
        function printReceipt() {{
            var mywindow = window.open('', 'PRINT', 'height=600,width=400');
            mywindow.document.write('<html><body>' + document.getElementById('receipt-content').innerHTML + '</body></html>');
            mywindow.document.close();
            mywindow.focus();
            mywindow.print();
            mywindow.close();
            return true;
        }}
    </script>
    <button onclick="printReceipt()" style="margin-top: 10px; padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
        🖨️ Print Receipt
    </button>
    """
    st.components.v1.html(final_html, height=500)
    
    if st.button("⬅️ Close", key="close_rec"): 
        st.session_state.update({"receipt": None, "receipt_totals": None, "receipt_no": None})
        st.rerun()

def format_currency(value):
    return f"{float(value):,.2f} MMK"

def get_session_val(key, default):
    return st.session_state.get(key, default)