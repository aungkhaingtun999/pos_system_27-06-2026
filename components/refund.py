import streamlit as st
import json

from components.supabase_logic import supabase, execute_refund


# =====================================================
# REFUND MANAGER
# =====================================================

def show_refund():

    st.title("🔄 Refund Manager")


    # =================================================
    # Session Message
    # =================================================

    if "msg" not in st.session_state:
        st.session_state.msg = None


    if st.session_state.msg:
        st.success(st.session_state.msg)
        st.session_state.msg = None



    # =================================================
    # Load Sales Data
    # =================================================

    try:

        response = (
            supabase
            .table("sales")
            .select("*")
            .order("id", desc=True)
            .execute()
        )

        sales_data = response.data or []


    except Exception as e:

        st.error(
            f"❌ Database Loading Error\n\n{e}"
        )

        return



    if not sales_data:

        st.info(
            "📭 No sales record found."
        )

        return



    # =================================================
    # Receipt Selection
    # =================================================

    receipt_options = {}

    for row in sales_data:

        receipt = row.get(
            "receipt_no",
            "Unknown"
        )

        status = row.get(
            "status",
            ""
        )


        label = (
            f"📄 {receipt}"
            +
            ("  [REFUNDED]" if status == "refunded" else "")
        )


        receipt_options[label] = row



    selected = st.selectbox(
        "🔍 Select Receipt:",
        [""] + list(receipt_options.keys())
    )



    if not selected:

        st.info(
            "Select a receipt to continue."
        )

        return



    invoice = receipt_options[selected]



    # =================================================
    # Already Refunded Check
    # =================================================

    if invoice.get("status") == "refunded":

        st.error(
            "⚠️ This receipt has already been refunded."
        )

        return



    receipt_no = invoice.get(
        "receipt_no",
        "-"
    )


    st.subheader(
        f"📋 Items in {receipt_no}"
    )



    # =================================================
    # Decode Items
    # =================================================

    try:

        raw_items = invoice.get(
            "item",
            []
        )


        if isinstance(raw_items, str):

            items = json.loads(
                raw_items
            )

        else:

            items = raw_items



    except Exception:

        st.error(
            "❌ Item data format error."
        )

        return



    if not items:

        st.warning(
            "No item found."
        )

        return



    # =================================================
    # Item Selection
    # =================================================

    selected_items = []

    total_refund = 0



    for index, item in enumerate(items):


        name = item.get(
            "product_name",
            "Unknown Item"
        )


        qty = int(
            item.get(
                "qty",
                1
            )
        )


        price = float(
            item.get(
                "sell_price",
                item.get(
                    "price",
                    0
                )
            )
        )



        col1, col2, col3 = st.columns(
            [0.5,0.25,0.25]
        )



        checked = col1.checkbox(
            name,
            key=f"refund_{invoice['id']}_{index}"
        )



        col2.write(
            f"Qty: {qty}"
        )


        col3.write(
            f"{price:,.0f} MMK"
        )



        if checked:

            selected_items.append(item)

            total_refund += (
                price * qty
            )



    st.divider()


    st.subheader(
        f"💰 Refund Amount: {total_refund:,.2f} MMK"
    )



    # =================================================
    # Confirm Button
    # =================================================


    if st.button(
        "⚠️ Confirm Refund",
        type="primary"
    ):


        if not selected_items:

            st.warning(
                "Please select item first."
            )

            return



        try:


            # -----------------------------------------
            # Final Database Check
            # -----------------------------------------

            check = (
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


            latest_status = (
                check.data.get("status")
                if check.data
                else None
            )



            if latest_status == "refunded":

                st.error(
                    "❌ Already refunded by another user."
                )

                return



            # -----------------------------------------
            # Execute Refund
            # -----------------------------------------

            refund_amount = execute_refund(
                invoice,
                selected_items
            )



            st.session_state.msg = (
                f"✅ Refund completed: "
                f"{refund_amount:,.2f} MMK"
            )


            st.rerun()



        except Exception as e:


            st.error(
                f"❌ Refund Failed\n\n{e}"
            )
