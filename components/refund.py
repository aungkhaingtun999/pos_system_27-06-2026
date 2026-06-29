import streamlit as st
import uuid
from datetime import datetime

from database import save_sale
from utils import show_receipt
from products import get_products_cached
from cart import add_to_cart, remove_from_cart, calculate_total


# ==========================================
# STOCK LOGIC IMPORT
# ==========================================

from components.stock_logic import (
    process_sale_stock_update
)


from components.supabase_logic import (
    sync_to_supabase
)


# =====================================================
# SAFE NUMBER
# =====================================================

def safe_float(value):

    try:

        if value is None:
            return 0.0


        if isinstance(value, str):

            value = value.replace(",", "")


        return float(value)


    except:

        return 0.0





# =====================================================
# GET PRICE
# =====================================================

def get_item_price(item):

    return safe_float(

        item.get("sell_price")

        or item.get("selling_price")

        or item.get("unit_price")

        or item.get("price")

        or item.get("amount")

        or 0

    )





# =====================================================
# GET QTY
# =====================================================

def get_item_qty(item):

    try:

        return int(

            item.get("qty")

            or

            item.get("quantity")

            or

            1

        )

    except:

        return 1





# =====================================================
# REFUND PAGE
# =====================================================

def show_refund():


    st.title(
        "🔄 Refund Manager"
    )



    # =============================================
    # SUCCESS MESSAGE
    # =============================================

    if "refund_success" in st.session_state:


        st.success(

            st.session_state[
                "refund_success"
            ]

        )


        del st.session_state[
            "refund_success"
        ]





    # =============================================
    # DATABASE CHECK
    # =============================================

    if not supabase:


        st.error(
            "Database Connection မရှိပါ"
        )

        return





    # =============================================
    # LOAD SALES
    # =============================================

    try:


        response = (

            supabase
            .table("sales")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()

        )


        sales = response.data or []



    except Exception as e:


        st.error(
            f"Sales Load Error : {e}"
        )

        return





    if not sales:


        st.info(
            "Sales Record မရှိပါ"
        )

        return





    # =============================================
    # RECEIPT SELECT
    # =============================================


    receipt_map = {}



    for sale in sales:


        label = (

            f"📄 {sale.get('receipt_no')}"

        )


        if sale.get("status") == "refunded":

            label += " ✅ REFUNDED"



        receipt_map[label] = sale





    selected = st.selectbox(

        "🔍 Select Receipt",

        [""] + list(receipt_map.keys())

    )





    if not selected:

        return




    invoice = receipt_map[selected]





    # =============================================
    # ALREADY REFUNDED
    # =============================================

    if invoice.get("status") == "refunded":


        st.warning(

            "⚠️ ဒီ Receipt ကို Refund ပြီးသားဖြစ်ပါသည်။"

        )

        return





    # =============================================
    # LOAD ITEMS
    # =============================================


    raw_items = invoice.get(
        "item",
        []
    )



    try:


        if isinstance(raw_items,str):

            items = json.loads(raw_items)

        else:

            items = raw_items



    except:


        st.error(
            "Item Data Error"
        )

        return





    if not items:


        st.warning(
            "ဒီ Receipt မှာ Item မရှိပါ"
        )

        return





    st.subheader(

        f"📋 Receipt : {invoice.get('receipt_no')}"

    )





    selected_items = []

    refund_total = 0





    # =============================================
    # ITEM LIST
    # =============================================


    for index,item in enumerate(items):


        qty = get_item_qty(item)


        price = get_item_price(item)



        name = item.get(

            "product_name",

            "Unknown Item"

        )



        c1,c2,c3 = st.columns(
            [0.5,0.25,0.25]
        )



        checked = c1.checkbox(

            name,

            key=f"refund_{invoice['id']}_{index}"

        )



        c2.write(

            f"Qty : {qty}"

        )


        c3.write(

            f"{price:,.0f} MMK"

        )




        if checked:


            selected_items.append(item)


            refund_total += (

                qty * price

            )





    st.divider()



    st.subheader(

        f"💰 Refund Amount : {refund_total:,.2f} MMK"

    )






    # =============================================
    # CONFIRM
    # =============================================


    if st.button(

        "⚠️ Confirm Refund",

        type="primary"

    ):



        if not selected_items:


            st.warning(
                "Item ရွေးပါ"
            )

            return




        if refund_total <= 0:


            st.error(
                "Refund Amount 0 ဖြစ်နေပါသည်"
            )

            return





        try:



            # 1. Refund Database

            amount = execute_refund(

                invoice,

                selected_items,

                refund_total

            )





            # 2. Stock Return

            try:


                process_refund_stock_update(

                    selected_items

                )


            except Exception as stock_error:


                st.warning(

                    f"Stock Update Warning : {stock_error}"

                )





            # 3. Success Message


            st.session_state[
                "refund_success"
            ] = (

                "✅ Refund အောင်မြင်ပါသည်\n\n"

                f"📄 Receipt : {invoice.get('receipt_no')}\n"

                f"💰 Amount : {amount:,.2f} MMK\n"

                "📦 Stock ပြန်တိုးပြီးပါပြီ"

            )



            st.rerun()





        except Exception as e:


            st.error(

                f"Refund Error : {e}"

            )
