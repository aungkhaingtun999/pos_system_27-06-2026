import streamlit as st
import json

from supabase import create_client
from datetime import datetime
import pytz



# =====================================================
# SUPABASE CONNECTION
# =====================================================

@st.cache_resource
def get_supabase_client():

    url = st.secrets.get(
        "SUPABASE_URL"
    )

    key = st.secrets.get(
        "SUPABASE_KEY"
    )


    if url and key:

        return create_client(
            url,
            key
        )


    return None



supabase = get_supabase_client()



# =====================================================
# TIME
# =====================================================

def get_myanmar_time():

    return datetime.now(
        pytz.timezone(
            "Asia/Yangon"
        )
    ).isoformat()



# =====================================================
# NUMBER
# =====================================================

def safe_float(value):

    try:

        if value is None:
            return 0.0


        if isinstance(value,str):

            value=value.replace(
                ",",
                ""
            )


        return float(value)


    except:

        return 0.0





# =====================================================
# SYNC SALES
# =====================================================

def sync_to_supabase(
        pending_sales=None
):


    if not supabase:

        raise Exception(
            "Database Connection မရှိပါ"
        )


    if not pending_sales:

        return False



    if not isinstance(
        pending_sales,
        list
    ):

        raise Exception(
            "Invalid sales data format"
        )



    try:


        for sale in pending_sales:



            data={


                "receipt_no":
                    sale.get(
                        "rec_no"
                    ),



                "customer_name":
                    sale.get(
                        "customer",
                        ""
                    ),



                "grand_total":
                    safe_float(

                        sale
                        .get(
                            "totals",
                            {}
                        )
                        .get(
                            "grand_total",
                            0
                        )

                    ),



                "payment_type":
                    sale.get(
                        "payment_method",
                        ""
                    ),



                "created_at":
                    get_myanmar_time(),



                "item":
                    json.dumps(
                        sale.get(
                            "cart",
                            []
                        ),
                        ensure_ascii=False
                    ),



                "totals":
                    json.dumps(
                        sale.get(
                            "totals",
                            {}
                        ),
                        ensure_ascii=False
                    ),



                "status":
                    "active"

            }



            supabase.table(
                "sales"
            ).insert(
                data
            ).execute()



        return True



    except Exception as e:


        raise Exception(
            f"Sync Failed : {e}"
        )






# =====================================================
# REFUND
# =====================================================

def execute_refund(
        inv,
        items_to_refund,
        refund_amount=None
):


    if not supabase:

        raise Exception(
            "Database Connection မရှိပါ"
        )


    try:



        # Status Check

        check=(

            supabase
            .table(
                "sales"
            )
            .select(
                "status"
            )
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


            raise Exception(
                "Already refunded"
            )





        # Calculate

        if refund_amount is None:


            refund_amount=0


            for item in items_to_refund:


                qty=int(
                    item.get(
                        "qty",
                        1
                    )
                )


                price=safe_float(
                    item.get(
                        "sell_price",
                        0
                    )
                )


                refund_amount += (

                    qty *
                    price

                )





        # Update sales status

        supabase.table(
            "sales"
        ).update(

            {
                "status":
                    "refunded"
            }

        ).eq(

            "id",
            inv["id"]

        ).execute()




        # Insert refund history


        supabase.table(
            "refunds"
        ).insert(

            {


            "receipt_no":
                inv.get(
                    "receipt_no"
                ),


            "items":
                json.dumps(
                    items_to_refund,
                    ensure_ascii=False
                ),


            "refund_amount":
                float(
                    refund_amount
                ),


            "refunded_at":
                get_myanmar_time(),


            "status":
                "completed"

            }

        ).execute()



        return refund_amount



    except Exception as e:


        raise Exception(
            f"Refund Failed : {e}"
        )
