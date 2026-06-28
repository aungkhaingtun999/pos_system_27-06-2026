import streamlit as st
import streamlit.components.v1 as components

def show_receipt(data, totals, receipt_no, payment_method, customer):
    # Receipt HTML/CSS
    items_html = ""
    for item in data:
        items_html += f"""
        <tr style="border-bottom: 1px dashed #ddd;">
            <td>{item.get('product_name')} x{item.get('qty')}</td>
            <td style="text-align: right;">{(float(item.get('sell_price', 0)) * int(item.get('qty', 1))):,.0f}</td>
        </tr>"""

    html_content = f"""
    <div id="printable-receipt" style="font-family: 'Courier New', monospace; padding: 10px; width: 280px; border: 1px solid #333;">
        <h2 style="text-align: center; margin: 0;">OFFICIAL RECEIPT</h2>
        <p style="font-size: 12px;">
            No: {receipt_no}<br>
            Customer: {customer}<br>
            Payment: {payment_method}<br>
            Date: {st.session_state.get('current_date', 'N/A')}
        </p>
        <table style="width: 100%; font-size: 12px;">
            {items_html}
        </table>
        <div style="text-align: right; font-size: 14px; margin-top: 10px;">
            <b>GRAND TOTAL: {totals.get('grand_total', 0):,.0f} MMK</b>
        </div>
    </div>
    """

    # Print လုပ်ဆောင်ချက်အတွက် JavaScript
    js_print = """
    <script>
        function printReceipt() {
            var printContents = document.getElementById('printable-receipt').innerHTML;
            var originalContents = document.body.innerHTML;
            document.body.innerHTML = printContents;
            window.print();
            document.body.innerHTML = originalContents;
        }
    </script>
    <button onclick="printReceipt()" style="width:100%; padding: 10px; background: #2e7d32; color: white; border: none; cursor: pointer;">
        🖨️ PRINT RECEIPT
    </button>
    """

    # UI ပြသခြင်း
    with st.popover("🧾 View Official Receipt", use_container_width=True):
        st.markdown(html_content, unsafe_allow_html=True)
        
        # Print ခလုတ် (HTML Component သုံးခြင်း)
        components.html(js_print, height=50)
        
        if st.button("⬅️ Close Receipt", use_container_width=True):
            st.session_state.receipt = None
            st.session_state.receipt_totals = None
            st.rerun()
