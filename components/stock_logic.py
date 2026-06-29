import streamlit as st
from datetime import datetime
import pytz

from components.supabase_logic import supabase


# =====================================================
# TIME
# =====================================================

def get_myanmar_time():

    return datetime.now(
        pytz.timezone(
            "Asia/Yangon"
        )
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )



# =====================================================
# NUMBER
# =====================================================

def safe_int(value):

    try:

        if value is None:
            return 0


        if isinstance(value, str):

            value = value.replace(",", "")


        return int(float(value))


    except:

        return 0



# =====================================================
# GET STOCK
# =====================================================

def get_product_stock(product_id):

    if not supabase:

        raise Exception(
            "Database Connection မရှိပါ"
        )


    result = (

        supabase
        .table("products")
        .select(
            "stock"
        )
        .eq(
            "id",
            product_id
        )
        .single()
        .execute()

    )


    if not result.data:

        raise Exception(
            f"Product ID {product_id} မတွေ့ပါ"
        )


    return safe_int(

        result.data.get(
            "stock",
            0
        )

    )



# =====================================================
# STOCK HISTORY
# =====================================================

def save_stock_history(
        product_id,
        qty_change,
        reason,
        before_stock,
        after_stock
):

    try:

        supabase.table(
            "stock_history"
        ).insert(

            {

                "product_id":
                    product_id,


                "qty_change":
                    qty_change,


                "reason":
                    reason,


                "before_stock":
                    before_stock,


                "after_stock":
                    after_stock,


                "created_at":
                    get_myanmar_time()

            }

        ).execute()


    except Exception:

        # History table error ဖြစ်လည်း POS မရပ်စေရ
        pass




# =====================================================
# MAIN UPDATE ENGINE
# =====================================================

def update_stock_db(
        product_id,
        qty_change,
        reason="SYSTEM"
):


    if not supabase:

        raise Exception(
            "Database Connection မရှိပါ"
        )


    if not product_id:

        raise Exception(
            "Product ID မရှိပါ"
        )



    qty_change = safe_int(
        qty_change
    )


    if qty_change == 0:

        return get_product_stock(
            product_id
        )



    # Before Stock

    before_stock = get_product_stock(
        product_id
    )


    after_stock = (

        before_stock
        +
        qty_change

    )



    # Stock Check

    if after_stock < 0:

        raise Exception(

            f"⚠️ Stock မလုံလောက်ပါ\n"
            f"လက်ကျန် : {before_stock}"

        )



    # Update Database

    update = (

        supabase
        .table("products")
        .update(

            {

                "stock":
                    after_stock

            }

        )
        .eq(

            "id",
            product_id

        )
        .execute()

    )



    # Verify

    verify = (

        supabase
        .table("products")
        .select(
            "stock"
        )
        .eq(
            "id",
            product_id
        )
        .single()
        .execute()

    )



    if not verify.data:

        raise Exception(
            "Stock Verify မအောင်မြင်ပါ"
        )



    current_stock = safe_int(

        verify.data.get(
            "stock"
        )

    )



    if current_stock != after_stock:

        raise Exception(

            "Stock Update မအောင်မြင်ပါ"

        )



    # Save History

    save_stock_history(

        product_id,

        qty_change,

        reason,

        before_stock,

        after_stock

    )



    return after_stock




# =====================================================
# SALE
# =====================================================

def process_sale_stock_update(cart):


    if not cart:

        return False



    for item in cart:


        product_id = (

            item.get("id")

            or

            item.get("product_id")

        )


        qty = safe_int(

            item.get(
                "qty",
                1
            )

        )


        if not product_id:

            continue



        if qty <= 0:

            continue



        update_stock_db(

            product_id,

            -qty,

            "SALE"

        )



    return True




# =====================================================
# REFUND
# =====================================================

def process_refund_stock_update(
        items_to_refund
):


    if not items_to_refund:

        return False



    for item in items_to_refund:


        product_id = (

            item.get("id")

            or

            item.get("product_id")

        )


        qty = safe_int(

            item.get(
                "qty",
                1
            )

        )


        if not product_id:

            continue



        if qty <= 0:

            continue



        update_stock_db(

            product_id,

            qty,

            "REFUND"

        )



    return True




# =====================================================
# RESTOCK
# =====================================================

def process_restock(
        product_id,
        qty
):


    qty = safe_int(
        qty
    )



    if qty <= 0:

        raise Exception(

            "Restock အရေအတွက် မှားနေပါသည်"

        )



    return update_stock_db(

        product_id,

        qty,

        "RESTOCK"

    )