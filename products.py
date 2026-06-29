# ==========================================
# 1. Imports
# ==========================================

import streamlit as st
import pandas as pd
from supabase import create_client
from config import SUPABASE_CONFIG



# ==========================================
# 2. SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def _get_client():

    if not SUPABASE_CONFIG["url"] or not SUPABASE_CONFIG["key"]:

        st.error(
            "Supabase credentials not found!"
        )

        return None


    return create_client(
        SUPABASE_CONFIG["url"],
        SUPABASE_CONFIG["key"]
    )



supabase = _get_client()





# ==========================================
# 3. SAFE NUMBER
# ==========================================

def safe_int(value):

    try:

        if value is None:
            return 0


        if isinstance(value,str):

            value=value.replace(",","")


        return int(float(value))


    except:

        return 0






# ==========================================
# 4. PRODUCT FETCH
# ==========================================


def get_inventory():

    """
    products table data အားလုံးရယူခြင်း
    """

    if not supabase:

        return pd.DataFrame()


    try:


        response = (

            supabase
            .table("products")
            .select("*")
            .execute()

        )


        if response.data:

            return pd.DataFrame(
                response.data
            )


        return pd.DataFrame()



    except Exception as e:


        st.error(
            f"Error fetching inventory : {e}"
        )

        return pd.DataFrame()





@st.cache_data(ttl=60)
def get_products_cached():


    df = get_inventory()


    if not df.empty:

        return df.to_dict(
            "records"
        )


    return []







# ==========================================
# 5. SEARCH
# ==========================================


def find_by_barcode(barcode):


    products = get_products_cached()


    return next(

        (
            p for p in products

            if str(
                p.get("barcode")
            )
            ==
            str(barcode)

        ),

        None

    )





def search_by_name(keyword):


    if not keyword:

        return []


    products=get_products_cached()


    return [

        p for p in products

        if keyword.lower()

        in str(
            p.get(
                "product_name",
                ""
            )
        ).lower()

    ]






# ==========================================
# 6. PRODUCT CRUD
# ==========================================


def add_new_product(product_data):


    try:


        response=(

            supabase
            .table("products")
            .insert(product_data)
            .execute()

        )


        st.cache_data.clear()


        return response



    except Exception as e:


        st.error(
            f"Error adding product : {e}"
        )

        return None







# ==========================================
# UPDATE STOCK
# ==========================================


def update_product_stock(
        barcode,
        new_stock
):


    try:


        response=(

            supabase
            .table("products")
            .update(
                {
                    "stock": safe_int(new_stock)
                }
            )
            .eq(
                "barcode",
                barcode
            )
            .execute()

        )


        st.cache_data.clear()


        return response



    except Exception as e:


        st.error(
            f"Error updating stock : {e}"
        )

        return None






# ==========================================
# UPDATE PRICE
# ==========================================


def update_product_price(
        barcode,
        new_buy_price,
        new_sell_price
):


    try:


        response=(

            supabase
            .table("products")
            .update(

                {

                    "buy_price":
                        float(new_buy_price),


                    "sell_price":
                        float(new_sell_price)

                }

            )
            .eq(
                "barcode",
                barcode
            )
            .execute()

        )


        st.cache_data.clear()


        return response



    except Exception as e:


        st.error(
            f"Error updating price : {e}"
        )

        return None






# ==========================================
# DELETE PRODUCT
# ==========================================


def delete_product(barcode):


    try:


        response=(

            supabase
            .table("products")
            .delete()
            .eq(
                "barcode",
                barcode
            )
            .execute()

        )


        st.cache_data.clear()


        return response



    except Exception as e:


        st.error(
            f"Error deleting product : {e}"
        )

        return None







# ==========================================
# STOCK UPDATE AFTER SALE
# ==========================================


def process_sale_stock_update(cart):

    """
    Sale ပြီးရင် stock လျှော့
    """


    if not cart:

        return False



    for item in cart:


        barcode = str(
            item.get(
                "barcode"
            )
        )


        product = find_by_barcode(
            barcode
        )


        if product:


            current_stock = safe_int(

                product.get(
                    "stock",
                    0
                )

            )


            qty = safe_int(

                item.get(
                    "qty",
                    0
                )

            )


            new_stock = current_stock - qty



            if new_stock < 0:

                raise Exception(

                    f"Stock မလုံလောက်ပါ : {barcode}"

                )



            update_product_stock(

                barcode,

                new_stock

            )


    st.cache_data.clear()


    return True






# ==========================================
# PROFIT CALCULATION
# ==========================================


def calculate_profit(cart):


    total = 0


    for item in cart:


        sell = float(
            item.get(
                "sell_price",
                0
            )
        )


        buy = float(
            item.get(
                "buy_price",
                0
            )
        )


        qty = safe_int(
            item.get(
                "qty",
                0
            )
        )


        total += (

            (sell-buy)

            *

            qty

        )


    return total






# ==========================================
# LOW STOCK
# ==========================================


def get_low_stock_products(
        threshold=5
):


    return [

        p for p in get_products_cached()

        if safe_int(
            p.get(
                "stock",
                0
            )
        )
        <= threshold

    ]
