import streamlit as st
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A7
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- PDF Font Setup (Myanmar Font) ---
# သင့်စက်ထဲမှ .ttf ဖိုင်လမ်းကြောင်းကို ထည့်ပေးပါ (ဥပမာ: "pyidaungsu.ttf")
# ဒီနေရာမှာ အလွယ်တကူရနိုင်တဲ့ default font ကိုပဲ အရင်သုံးထားပါတယ်
def setup_fonts():
    try:
        # pdfmetrics.registerFont(TTFont('Myanmar', 'Pyidaungsu.ttf'))
        pass 
    except:
        pass

# --- PDF Generation Logic ---
def generate_pdf_receipt(data, totals, receipt_no, payment_method, customer):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(200, 400))
    y = 380
    
    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "OFFICIAL RECEIPT")
    y -= 20
    
    # Header Info
    c.setFont("Helvetica", 8)
    c.drawString(20, y, f"No: {receipt_no}")
    y -= 10
    c.drawString(20, y, f"Customer: {customer}")
    y -= 10
    c.drawString(20, y, f"Payment: {payment_method}")
    y -= 20
    
    # Items
    c.drawString(20, y, "------------------------------------------------")
    y -= 15
    for item in data:
        price = float(item.get('sell_price') or item.get('price', 0))
        qty = float(item.get('qty', 0))
        line_total = qty * price
        c.drawString(20, y, f"{item.get('product_name')[:20]} x{qty:.0f}")
        c.drawRightString(180, y, f"{line_total:,.0f}")
        y -= 12
    
    c.drawString(20, y, "------------------------------------------------")
    y -= 15
    
    # Totals
    c.drawString(20, y, f"Subtotal: {totals.get('subtotal', 0):,.0f}")
    y -= 10
    c.drawString(20, y, f"Tax: {totals.get('tax', 0):,.0f}")
    y -= 10
    c.drawString(20, y, f"Discount: {totals.get('discount', 0):,.0f}")
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20, y, f"GRAND TOTAL: {totals.get('grand_total', 0):,.0f} MMK")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- Updated UI Dialog ---
@st.dialog("🧾 Official Receipt")
def show_receipt(data, totals, receipt_no, payment_method="Cash", customer="Walk-in"):
    items_text = ""
    for item in data:
        price = float(item.get('sell_price') or item.get('price', 0))
        qty = float(item.get('qty', 0))
        line_total = qty * price
        items_text += f"{item.get('product_name')} | {qty:.0f} x {price:,.0f} = {line_total:,.0f} MMK\n"
    
    st.text(f"No: {receipt_no}\nCustomer: {customer}\nPayment: {payment_method}\n"
            f"-----------------------------\n{items_text}"
            f"-----------------------------\n"
            f"GRAND TOTAL: {totals.get('grand_total', 0):,.0f} MMK")
    
    # PDF Download Button
    pdf_data = generate_pdf_receipt(data, totals, receipt_no, payment_method, customer)
    st.download_button(
        label="📥 Download PDF Receipt",
        data=pdf_data,
        file_name=f"Receipt_{receipt_no}.pdf",
        mime="application/pdf"
    )
    
    if st.button("⬅️ Close", key="close_rec"): 
        st.session_state.receipt = None
        st.session_state.receipt_totals = None
        st.session_state.receipt_no = None
        st.rerun()