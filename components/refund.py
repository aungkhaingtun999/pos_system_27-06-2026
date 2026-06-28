import streamlit as st
import json

from components.supabase_logic import (
    supabase,
    execute_refund
)



# =====================================================
# SAFE FLOAT
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
# REFUND MANAGER
# =====================================================

def show_refund():


    st.title(
        "🔄 Refund Manager"
    )



    # =====================================
    # Message
    # =====================================

    if "msg" not in st.session_state:

        st.session_state.msg = None



    if st.session_state.msg:


        st.success(
            st.session_state.msg
        )


        st.session_state.msg = None




    # =====================================
    # Load Sales
    # =====================================

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
            "No sales record found."
        )

        return





    # =====================================
    # Receipt Select
    # =====================================

    options = {}


    for row in sales_data:


        receipt = row.get(
            "receipt_no",
            "-"
        )


        status = row.get(
            "status",
            ""
        )


        label = (

            f"📄 {receipt}"

            +

            (
                " [REFUNDED]"
                if status=="refunded"
                else ""
            )

        )


        options[label] = row




    selected = st.selectbox(

        "🔍 Select Receipt to Refund:",

        [""] + list(options.keys())

    )



    if not selected:

        return




    inv = options[selected]




    # =====================================
    # Status Check
    # =====================================


    if inv.get("status") == "refunded":


        st.error(

            "⚠️ ဤပြေစာအား Refund လုပ်ပြီးသားဖြစ်ပါသည်။"

        )


        return




    # =====================================
    # Load Items
    # =====================================


    try:


        raw_items = inv.get(
            "item",
            []
        )


        if isinstance(
            raw_items,
            str
        ):


            items = json.loads(
                raw_items
            )


        else:


            items = raw_items



    except Exception as e:


        st.error(
            f"Item Decode Error : {e}"
        )

        return




    if not items:


        st.warning(
            "No items found."
        )

        return




    st.subheader(

        f"📋 Items in {inv.get('receipt_no')}"

    )





    # =====================================
    # Item Selection
    # =====================================

    selected_items = []

    refund_total = 0.0



    for i,item in enumerate(items):


        product_name = item.get(
            "product_name",
            "Unknown"
        )


        qty = int(
            item.get(
                "qty",
                1
            )
        )


        sell_price = safe_float(

            item.get(
                "sell_price",
                0
            )

        )


        amount = sell_price * qty




        col1,col2,col3 = st.columns(
            [0.5,0.25,0.25]
        )



        checked = col1.checkbox(

            product_name,

            key=f"refund_{inv['id']}_{i}"

        )



        col2.write(

            f"Qty : {qty}"

        )


        col3.write(

            f"{sell_price:,.2f} MMK"

        )



        if checked:


            selected_items.append(
                item
            )


            refund_total += amount





    st.divider()



    st.subheader(

        f"💰 Refund Amount : {refund_total:,.2f} MMK"

    )





    # =====================================
    # Confirm Button
    # =====================================


    if st.button(

        "⚠️ Confirm Process Refund",

        type="primary"

    ):



        if not selected_items:


            st.warning(

                "Please select at least one item."

            )

            return




        try:



            # Last DB Check

            check = (

                supabase
                .table("sales")
                .select("status")
                .eq(
                    "id",
                    inv["id"]
                )
                .single()
                .execute()

            )



            if (

                check.data

                and

                check.data.get(
                    "status"
                )
                ==
                "refunded"

            ):


                st.error(

                    "❌ Already refunded."

                )

                return




            # =================================
            # Execute Refund
            # =================================


            processed = execute_refund(

                inv,

                selected_items,

                refund_total

            )



            st.session_state.msg = (

                f"✅ Refund "
                f"{processed:,.2f} MMK completed!"

            )



            st.rerun()




        except Exception as e:


            st.error(

                f"Refund Error : {e}"

            )
