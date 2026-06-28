import streamlit as st
import pandas as pd

def show_receipt(data, totals, receipt_no, payment_method, customer):
    # Receipt ကို HTML String အနေဖြင့် တည်ဆောက်ခြင်း
    items_html = ""
    for item in data:
        items_html += f"<li>{item.get('product_name')} x{item.get('qty')} : {item.get('sell_price', 0):,.0f} MMK</li>"

    html_content = f"""
    <div id="printable-receipt" style="font-family: sans-serif; padding: 20px; width: 300px; border: 1px solid #ccc;">
        <h3>OFFICIAL RECEIPT</h3>
        <p>No: {receipt_no}<br>Customer: {customer}<br>Payment: {payment_method}</p>
        <hr>
        <ul>{items_html}</ul>
        <hr>
        <p>Subtotal: {totals.get('subtotal', 0):,.0f} MMK<br>
           Tax: {totals.get('tax', 0):,.0f} MMK<br>
           Discount: {totals.get('discount', 0):,.0f} MMK</p>
        <h4>GRAND TOTAL: {totals.get('grand_total', 0):,.0f} MMK</h4>
    </div>
    """

    with st.popover("🧾 View Official Receipt", use_container_width=True):
        # မျက်နှာပြင်ပေါ်တွင် HTML ပြသခြင်း
        st.markdown(html_content, unsafe_allow_html=True)
        
        # Print ခလုတ် (JavaScript သုံး၍)
        if st.button("🖨️ Print Receipt", key=f"print_{receipt_no}"):
            # Print အတွက် JavaScript
            js = f"""
            <script>
                var printContents = `{html_content}`;
                var originalContents = document.body.innerHTML;
                document.body.innerHTML = printContents;
                window.print();
                document.body.innerHTML = originalContents;
                window.location.reload();
            </script>
            """
            st.markdown(js, unsafe_allow_html=True)
        
        if st.button("⬅️ Close Receipt", key=f"close_{receipt_no}"):
            st.session_state.receipt = None
            st.rerun()