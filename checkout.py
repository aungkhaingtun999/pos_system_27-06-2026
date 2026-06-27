# ==========================================
# 1. Imports
# ==========================================
from database import (
    insert_sales_master,
    insert_sales_detail,
    update_stock
)
from utils import (
    generate_invoice, 
    calc_discount, 
    calc_tax, 
    calc_grand_total
)

# ==========================================
# 2. Helper Functions (Logic & Formatting)
# ==========================================
def _prepare_sales_master(invoice_no, customer_name, payment_type, totals):
    """Sales Master အတွက် လိုအပ်သော data dictionary ကို ပြင်ဆင်ပေးခြင်း"""
    return {
        "invoice_no": invoice_no,
        "customer_name": customer_name,
        "payment_type": payment_type,
        "subtotal": totals["subtotal"],
        "discount": totals["discount"],
        "tax": totals["tax"],
        "grand_total": totals["grand_total"]
    }

def _prepare_sales_detail(sale_id, item):
    """Sales Detail အတွက် လိုအပ်သော data dictionary ကို ပြင်ဆင်ပေးခြင်း"""
    return {
        "sale_id": sale_id,
        "product_id": item["id"],
        "product_name": item["name"],
        "qty": item["qty"],
        "price": item["price"],
        "total": item["total"]
    }

def save_invoice_text(invoice_no, content):
    """Unicode(UTF-8) ဖြင့် Invoice ကို Text ဖိုင်အဖြစ် သိမ်းဆည်းပေးခြင်း"""
    file_name = f"invoice_{invoice_no}.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    return file_name

# ==========================================
# 3. Main Run Module (Process Checkout)
# ==========================================
def process_checkout(cart, customer_name, payment_type, discount_percent, tax_percent):
    """Main checkout process: Calculations, Database saving, and Stock update"""
    
    if not cart:
        return {"status": "error", "message": "Cart is empty"}

    # Calculations
    subtotal = sum(item["total"] for item in cart)
    discount = calc_discount(subtotal, discount_percent)
    tax = calc_tax(subtotal - discount, tax_percent)
    grand_total = calc_grand_total(subtotal, discount, tax)
    
    totals = {"subtotal": subtotal, "discount": discount, "tax": tax, "grand_total": grand_total}

    # Generate Invoice Number
    invoice_no = generate_invoice()

    # Save Sales Master
    master_data = _prepare_sales_master(invoice_no, customer_name, payment_type, totals)
    sale = insert_sales_master(master_data)

    if not sale:
        return {"status": "error", "message": "Failed to save sale"}

    sale_id = sale["id"]

    # Save Sales Detail & Update Stock
    for item in cart:
        # Save Detail
        insert_sales_detail(_prepare_sales_detail(sale_id, item))

        # Update Stock
        current_stock = item.get("stock", 0)
        update_stock(item["id"], current_stock - item["qty"])

    return {
        "status": "success",
        "invoice_no": invoice_no,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "grand_total": grand_total,
        "sale_id": sale_id
    }