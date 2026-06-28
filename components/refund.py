import streamlit as st
import json

from components.supabase_logic import (
    supabase,
    execute_refund
)



# =====================================================
# NUMBER FORMAT
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
# REFUND PAGE
# =====================================================

def show_refund():

    st.title(
        "🔄 Refund Manager"
    )


    # ==========================================
    # SUCCESS MESSAGE
    # ==========================================

    if "refund_success" in st.session_state:

        st.success(
            st.session_state["refund_success"]
        )

        del st.session_state["refund_success"]




    # ==========================================
    # LOAD SALES
    # ==========================================

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


        sales_data = response.data or []


    except Exception as e:

        st.error(
            f"Database Error : {e}"
        )

        return





    if not sales_data:

        st.info(
            "Sales record မရှိပါ"
        )

        return





    # ==========================================
    # RECEIPT SELECT
    # ==========================================

    options = {}


    for sale in sales_data:


        label = (
            f"📄 {sale.get('receipt_no')}"
        )


        if sale.get("status") == "refunded":

            label += " [REFUNDED]"


        options[label] = sale





    selected = st.selectbox(

        "🔍 Select Receipt",

        [""] + list(options.keys())

    )



    if not selected:

        return




    inv = options[selected]





    # ==========================================
    # BLOCK ALREADY REFUNDED
    # ==========================================

    if inv.get("status") == "refunded":


        st.error(
            "⚠️ ဒီ Receipt ကို Refund လုပ်ပြီးသားဖြစ်ပါသည်။"
        )

        return





    # ==========================================
    # LOAD ITEMS
    # ==========================================

    raw_items = inv.get(
        "item",
        []
    )



    try:

        if isinstance(raw_items, str):

            items = json.loads(raw_items)

        else:

            items = raw_items


    except:


        st.error(
            "Item Data ဖတ်၍မရပါ"
        )

        return





    st.subheader(

        f"📋 {inv.get('receipt_no')}"

    )





    selected_items = []

    refund_total = 0.0





    # ==========================================
    # ITEM LIST
    # ==========================================

    for i, item in enumerate(items):


        qty = int(

            item.get("qty")

            or

            item.get("quantity")

            or

            1

        )



        price = safe_float(

            item.get("sell_price")

            or

            item.get("selling_price")

            or

            item.get("unit_price")

            or

            item.get("price")

            or

            item.get("amount")

            or

            0

        )




        col1, col2, col3 = st.columns(
            [0.5, 0.25, 0.25]
        )



        checked = col1.checkbox(

            item.get(
                "product_name",
                "Item"
            ),

            key=f"refund_{inv['id']}_{i}"

        )



        col2.write(
            f"Qty : {qty}"
        )


        col3.write(
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





    # ==========================================
    # CONFIRM REFUND
    # ==========================================

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


            result = execute_refund(

                inv,

                selected_items,

                refund_total

            )



            # ==================================
            # SUCCESS
            # ==================================

            st.session_state["refund_success"] = (

                f"✅ Refund အောင်မြင်ပါသည်\n\n"

                f"📄 Receipt : {inv.get('receipt_no')}\n"

                f"💰 Amount : {result:,.2f} MMK"

            )



            st.rerun()




        except Exception as e:


            st.error(

                f"Refund Error : {e}"

            )
