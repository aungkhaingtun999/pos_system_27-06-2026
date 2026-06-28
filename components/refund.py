import streamlit as st
import json

from components.supabase_logic import (
    supabase,
    execute_refund
)



# =====================================================
# NUMBER FORMAT
# =====================================================

def convert_number(value):

    try:

        if value is None:
            return 0.0


        if isinstance(value,str):

            value=value.replace(",","")


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



    # ==============================
    # Message
    # ==============================

    if "msg" not in st.session_state:

        st.session_state.msg=None



    if st.session_state.msg:


        st.success(
            st.session_state.msg
        )


        st.session_state.msg=None




    # ==============================
    # Load Sales
    # ==============================

    try:


        response=(

            supabase
            .table("sales")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()

        )


        sales=response.data or []



    except Exception as e:


        st.error(
            f"Database Error : {e}"
        )

        return




    if not sales:


        st.warning(
            "No Sales Found"
        )

        return




    # ==============================
    # Receipt Select
    # ==============================


    receipts={}


    for sale in sales:


        receipt=sale.get(
            "receipt_no",
            "-"
        )


        status=sale.get(
            "status",
            ""
        )



        title=(

            f"📄 {receipt}"

            +

            (
                " [REFUNDED]"
                if status=="refunded"
                else ""
            )

        )


        receipts[title]=sale




    selected=st.selectbox(

        "🔍 Select Receipt:",

        [""]+
        list(receipts.keys())

    )



    if not selected:

        return




    invoice=receipts[selected]



    if invoice.get("status")=="refunded":


        st.error(
            "⚠️ This receipt already refunded"
        )


        return




    st.subheader(

        f"📋 Items in {invoice.get('receipt_no')}"

    )




    # ==============================
    # Load Items
    # ==============================


    try:


        items_data=invoice.get(
            "item",
            []
        )


        if isinstance(
            items_data,
            str
        ):

            items=json.loads(
                items_data
            )

        else:

            items=items_data



    except Exception as e:


        st.error(
            f"Item Decode Error : {e}"
        )


        return




    selected_items=[]

    refund_amount=0




    # ==============================
    # Item List
    # ==============================


    for index,item in enumerate(items):


        product_name=item.get(
            "product_name",
            "Unknown"
        )



        qty=int(
            item.get(
                "qty",
                1
            )
        )



        sell_price=convert_number(

            item.get(
                "sell_price"
            )

        )



        total=sell_price * qty



        c1,c2,c3=st.columns(
            [0.5,0.25,0.25]
        )



        checked=c1.checkbox(

            product_name,

            key=f"refund_{invoice['id']}_{index}"

        )



        c2.write(
            f"Qty : {qty}"
        )



        c3.write(

            f"{sell_price:,.2f} MMK"

        )



        if checked:


            selected_items.append(
                item
            )


            refund_amount += total




    st.divider()



    st.subheader(

        f"💰 Refund Amount : {refund_amount:,.2f} MMK"

    )





    # ==============================
    # Confirm Refund
    # ==============================


    if st.button(

        "⚠️ Confirm Refund",

        type="primary"

    ):



        if not selected_items:


            st.warning(
                "Please select item"
            )

            return




        try:



            # Double Check Status

            check=(

                supabase
                .table("sales")
                .select("status")
                .eq(
                    "id",
                    invoice["id"]
                )
                .single()
                .execute()

            )



            if (

                check.data

                and

                check.data.get("status")
                ==
                "refunded"

            ):


                st.error(
                    "Already refunded"
                )

                return




            # =====================
            # Execute Refund
            # =====================


            result=execute_refund(

                invoice,

                selected_items,

                refund_amount

            )



            # if function return none

            if result is None:

                result=refund_amount




            st.session_state.msg=(

                f"✅ Refund completed : "
                f"{result:,.2f} MMK"

            )



            st.rerun()




        except Exception as e:


            st.error(

                f"Refund Error : {e}"

            )
