import streamlit as st
import uuid
from datetime import datetime


from database import save_sale
from utils import show_receipt
from products import get_products_cached
from cart import (
    add_to_cart,
    remove_from_cart,
    calculate_total
)


from components.supabase_logic import (
    sync_to_supabase
)


from components.stock_logic import (
    process_sale_stock_update
)



# ==========================================
# HELPER
# ==========================================

def _get_product_price(product):

    return float(
        product.get("sell_price")
        or product.get("price")
        or 0
    )



def _generate_receipt_no():

    today = datetime.now().strftime("%Y%m%d")

    unique = uuid.uuid4().hex[:6].upper()

    return f"INV-{today}-{unique}"




# ==========================================
# CHECKOUT
# ==========================================

def _process_checkout(
        cart,
        totals,
        payment_method,
        customer_name
):


    receipt_no = _generate_receipt_no()


    customer = (
        customer_name
        if customer_name
        else "Walk-in"
    )


    try:


        # 1. Save Local

        save_sale(

            cart,

            totals,

            receipt_no=receipt_no,

            payment_method=payment_method,

            customer_name=customer

        )



        # 2. Reduce Stock

        process_sale_stock_update(
            cart
        )



        # 3. Pending Cloud Sync

        if "pending_sales" not in st.session_state:

            st.session_state.pending_sales=[]



        st.session_state.pending_sales.append({

            "cart":cart,

            "totals":totals,

            "rec_no":receipt_no,

            "payment_method":payment_method,

            "customer":customer

        })



        return receipt_no, customer



    except Exception as e:


        raise Exception(
            f"Checkout Failed : {e}"
        )





# ==========================================
# MAIN POS
# ==========================================

def show_pos_system():


    st.title(
        "💰 POS System"
    )



    # ==========================
    # INIT SESSION
    # ==========================


    if "barcode_input" not in st.session_state:

        st.session_state.barcode_input=""


    if "cart" not in st.session_state:

        st.session_state.cart=[]


    if "prod_select" not in st.session_state:

        st.session_state.prod_select=""





    # ==========================
    # SYNC
    # ==========================


    if st.session_state.get(
        "pending_sales"
    ):


        st.warning(

            f"⚠️ Sync မလုပ်ရသေးသော အရောင်း "
            f"{len(st.session_state.pending_sales)} ခု"

        )



        if st.button(
            "🔄 Sync Cloud"
        ):


            try:


                sync_to_supabase(

                    st.session_state.pending_sales

                )


                st.session_state.pending_sales=[]


                st.success(
                    "✅ Sync အောင်မြင်ပါသည်"
                )


                st.rerun()



            except Exception as e:


                st.error(
                    f"Sync Error : {e}"
                )





    # ==========================
    # RECEIPT
    # ==========================


    if st.session_state.get(
        "receipt"
    ):


        show_receipt(

            st.session_state.receipt,

            st.session_state.receipt_totals,

            st.session_state.receipt_no,

            st.session_state.get(
                "current_payment_method",
                "Cash"
            ),

            st.session_state.get(
                "current_customer",
                "Walk-in"
            )

        )


        if st.button(
            "🖨️ Close Receipt"
        ):

            st.session_state.receipt=None

            st.rerun()



        st.divider()






    # ==========================
    # PRODUCTS
    # ==========================


    products=get_products_cached()


    if not products:

        st.warning(
            "Product မရှိပါ"
        )

        return



    product_map={

        str(x.get("barcode")):x

        for x in products

    }



    product_options={


        f"{x.get('product_name')} | "
        f"{_get_product_price(x):,.0f} MMK":

        x

        for x in products

    }




    # ==========================
    # BARCODE
    # ==========================


    st.text_input(

        "🔫 Barcode Scan",

        key="barcode_input",

        on_change=barcode_add

    )




    # ==========================
    # SEARCH
    # ==========================


    st.selectbox(

        "🔍 Product Search",

        [""] + list(product_options.keys()),

        key="prod_select",

        on_change=lambda:
            search_add(product_options)

    )






    # ==========================
    # CART
    # ==========================


    for i,item in enumerate(
        st.session_state.cart
    ):


        c1,c2,c3=st.columns(
            [3,1,1]
        )


        c1.write(
            item.get("product_name")
        )



        item["qty"]=c2.number_input(

            "Qty",

            min_value=1,

            value=int(item.get("qty",1)),

            key=f"qty_{i}"

        )



        if c3.button(
            "❌",
            key=f"delete_{i}"
        ):


            st.session_state.cart = remove_from_cart(

                st.session_state.cart,

                i

            )

            st.rerun()





    # ==========================
    # CHECKOUT
    # ==========================


    if st.session_state.cart:


        tax_rate = st.number_input(
            "Tax %",
            value=0.0
        ) / 100



        discount = st.number_input(
            "Discount",
            value=0
        )



        totals = calculate_total(

            st.session_state.cart,

            tax_rate,

            discount

        )



        st.subheader(

            f"Grand Total : "
            f"{totals['grand_total']:,.0f} MMK"

        )



        payment_method=st.selectbox(

            "💳 Payment",

            [
                "Cash",
                "Credit (အကြွေး)",
                "Installment (အရစ်ကျ)"
            ]

        )


        customer=st.text_input(
            "👤 Customer"
        )



        if st.button(
            "✅ Confirm Checkout"
        ):


            try:


                rec,customer=_process_checkout(

                    st.session_state.cart,

                    totals,

                    payment_method,

                    customer

                )



                st.session_state.update({

                    "receipt":
                        st.session_state.cart.copy(),

                    "receipt_totals":
                        totals,

                    "receipt_no":
                        rec,

                    "current_payment_method":
                        payment_method,

                    "current_customer":
                        customer,

                    "cart":[]

                })


                st.success(
                    "✅ အရောင်းအောင်မြင်ပါသည်"
                )


                st.rerun()



            except Exception as e:


                st.error(
                    str(e)
                )





# ==========================================
# BARCODE FUNCTION
# ==========================================

def barcode_add():


    code=str(

        st.session_state.get(
            "barcode_input",
            ""
        )

    ).strip()



    if not code:

        return



    products=get_products_cached()



    mapping={

        str(x.get("barcode")):x

        for x in products

    }



    if code in mapping:


        st.session_state.cart = add_to_cart(

            st.session_state.cart,

            mapping[code]

        )


    else:

        st.warning(
            "Barcode မတွေ့ပါ"
        )



    st.session_state.barcode_input=""






# ==========================================
# SEARCH FUNCTION
# ==========================================

def search_add(product_options):


    selected = st.session_state.get(
        "prod_select"
    )


    if selected:


        st.session_state.cart = add_to_cart(

            st.session_state.cart,

            product_options[selected]

        )
