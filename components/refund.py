import streamlit as st
import json

from components.supabase_logic import (
    supabase,
    execute_refund
)


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

    st.title("🔄 Refund Manager")


    # Load Sales

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




    # Select Receipt

    options = {

        f"📄 {x.get('receipt_no')}": x

        for x in sales_data

    }


    selected = st.selectbox(
        "🔍 Select Receipt",
        [""] + list(options.keys())
    )



    if not selected:

        return



    inv = options[selected]



    if inv.get("status") == "refunded":

        st.error(
            "⚠️ ဒီ Receipt ကို Refund လုပ်ပြီးသားဖြစ်ပါသည်။"
        )

        return





    # Load Items

    raw_items = inv.get(
        "item",
        []
    )


    if isinstance(raw_items,str):

        items = json.loads(raw_items)

    else:

        items = raw_items





    st.subheader(
        f"📋 {inv.get('receipt_no')}"
    )



    selected_items=[]

    refund_total=0.0





    for i,item in enumerate(items):


        qty=int(
            item.get(
                "qty",
                1
            )
        )


        price = safe_float(
    item.get("sell_price")
    or item.get("selling_price")
    or item.get("unit_price")
    or item.get("price")
    or item.get("amount")
    or 0
)


        col1,col2,col3 = st.columns(
            [0.5,0.25,0.25]
        )


        checked=col1.checkbox(
            item.get(
                "product_name",
                "Item"
            ),
            key=f"refund_{inv['id']}_{i}"
        )


        col2.write(
            f"Qty {qty}"
        )


        col3.write(
            f"{price:,.0f}"
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




    if st.button(
        "⚠️ Confirm Refund"
    ):


        if not selected_items:


            st.warning(
                "Item ရွေးပါ"
            )

            return



        try:


            result = execute_refund(

                inv,

                selected_items,

                refund_total

            )


            st.success(
                f"✅ Refund {result:,.2f} MMK Completed"
            )


            st.rerun()



        except Exception as e:


            st.error(
                str(e)
            )
# ==========================================
# 5. Update Sales Status
# ==========================================

supabase.table(
    "sales"
).update(

    {
        "status": "refunded"
    }

).eq(

    "id",
    invoice_id

).execute()



# Verify Update

verify = (

    supabase
    .table("sales")
    .select(
        "status"
    )
    .eq(
        "id",
        invoice_id
    )
    .single()
    .execute()

)



if not verify.data:

    raise Exception(
        "Sales record မတွေ့ပါ"
    )



if verify.data.get("status") != "refunded":

    raise Exception(
        "Sales Status Update မအောင်မြင်ပါ"
    )
