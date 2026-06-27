# ==========================
# MAIN APP
# PHASE 3 POS SYSTEM
# ==========================

import streamlit as st


from config import APP_NAME, init_session
from utils import money

from products import (
    load_products,
    find_by_barcode,
    search_by_name
)

from cart import (
    add_to_cart,
    update_qty,
    clear_cart,
    cart_summary
)

from checkout import process_checkout

from auth import login, check_login

from dashboard import show_dashboard



# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)



# ==========================
# SESSION INIT
# ==========================

init_session()



# ==========================
# LOGIN
# ==========================

login()

if not check_login():
    st.stop()



# ==========================
# LOAD PRODUCTS
# ==========================

products = load_products()



# ==========================
# TITLE
# ==========================

st.title("💰 Barcode POS System")



# ==========================
# MENU
# ==========================

menu = st.sidebar.radio(

    "MENU",

    [
        "POS",
        "Dashboard",
        "Stock",
        "Report"
    ]

)



cart = st.session_state.cart



# ==========================
# POS
# ==========================

if menu == "POS":


    st.subheader("📷 Barcode Scanner")


    barcode = st.text_input(
        "Scan Barcode"
    )


    if barcode:


        product = find_by_barcode(barcode)


        if product:


            st.session_state.cart = add_to_cart(
                cart,
                product
            )

            st.success(
                f"{product['product_name']} Added"
            )

            st.rerun()


        else:

            st.error(
                "Product not found"
            )



    # ======================
    # SEARCH
    # ======================


    st.divider()

    st.subheader(
        "🔍 Product Search"
    )


    keyword = st.text_input(
        "Search Product"
    )


    if keyword:


        results = search_by_name(
            products,
            keyword
        )


        for p in results:


            c1,c2,c3 = st.columns(
                [3,2,1]
            )


            c1.write(
                p["product_name"]
            )


            c2.write(
                money(p["sell_price"])
            )


            if c3.button(
                "Add",
                key=p["id"]
            ):


                st.session_state.cart = add_to_cart(
                    cart,
                    p
                )

                st.rerun()



    # ======================
    # CART
    # ======================


    st.divider()

    st.subheader(
        "🛒 Cart"
    )


    if cart:


        for i,item in enumerate(cart):


            c1,c2,c3,c4,c5 = st.columns(
                [3,1,1,1,1]
            )


            c1.write(
                item["name"]
            )


            c2.write(
                money(item["price"])
            )


            if c3.button(
                "+",
                key=f"plus{i}"
            ):

                st.session_state.cart = update_qty(
                    cart,
                    i,
                    "plus"
                )

                st.rerun()



            c4.write(
                item["qty"]
            )



            if c5.button(
                "-",
                key=f"minus{i}"
            ):


                st.session_state.cart = update_qty(
                    cart,
                    i,
                    "minus"
                )

                st.rerun()



        summary = cart_summary(cart)


        st.success(
            f"Subtotal : {summary['formatted']} MMK"
        )



        if st.button(
            "Clear Cart"
        ):

            st.session_state.cart = clear_cart()

            st.rerun()



    else:

        st.info(
            "Cart Empty"
        )



    # ======================
    # CHECKOUT
    # ======================


    st.divider()

    st.subheader(
        "💳 Checkout"
    )


    customer = st.text_input(
        "Customer Name",
        "Walk-in Customer"
    )


    payment = st.selectbox(

        "Payment",

        [
            "Cash",
            "KBZ Pay",
            "Wave Money",
            "Card"
        ]

    )


    discount = st.number_input(
        "Discount %",
        0.0
    )


    tax = st.number_input(
        "Tax %",
        0.0
    )



    if st.button(
        "🔴 Confirm Sale"
    ):


        result = process_checkout(

            cart,
            customer,
            payment,
            discount,
            tax

        )



        if result["status"] == "success":


            st.success(
                "Sale Complete"
            )


            st.write(
                "Invoice:",
                result["invoice_no"]
            )


            st.write(
                "Total:",
                money(result["grand_total"]),
                "MMK"
            )


            st.session_state.cart = []


        else:


            st.error(
                result["message"]
            )



# ==========================
# DASHBOARD
# ==========================

elif menu == "Dashboard":

    show_dashboard()



# ==========================
# STOCK
# ==========================

elif menu == "Stock":


    st.subheader(
        "📦 Stock"
    )


    st.dataframe(
        products,
        use_container_width=True
    )



# ==========================
# REPORT
# ==========================

elif menu == "Report":


    st.subheader(
        "📊 Report"
    )


    st.info(
        "Report Module Coming Soon"
    )