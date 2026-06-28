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

    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")


    if url and key:

        return create_client(
            url,
            key
        )


    return None



supabase = get_supabase_client()





# =====================================================
# MYANMAR TIME
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
# SAFE NUMBER
# =====================================================

def safe_float(value):

    try:

        if value is None:
            return 0.0


        if isinstance(value,str):

            value=value.replace(",","")


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
            "Invalid sales data"
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
# =====================================================
# REFUND PROCESS
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


        receipt_no = inv.get(
            "receipt_no"
        )

        invoice_id = inv.get(
            "id"
        )


        if not receipt_no or not invoice_id:

            raise Exception(
                "Receipt Data မပြည့်စုံပါ"
            )



        # ==========================================
        # 1. Check Current Sales Status
        # ==========================================

        sales_check = (

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


        if sales_check.data:


            status = sales_check.data.get(
                "status"
            )


            if status == "refunded":

                raise Exception(
                    "⚠️ ဒီ Receipt ကို Refund လုပ်ပြီးသားဖြစ်ပါသည်။"
                )






        # ==========================================
        # 2. Check Refund History
        # ==========================================

        refund_check = (

            supabase
            .table("refunds")
            .select(
                "id"
            )
            .eq(
                "receipt_no",
                receipt_no
            )
            .execute()

        )


        if refund_check.data:


            raise Exception(
                "⚠️ ဒီ Receipt အတွက် Refund History ရှိပြီးသားဖြစ်ပါသည်။"
            )






        # ==========================================
        # 3. Calculate Refund Amount
        # ==========================================

        if refund_amount is None:


            refund_amount = 0.0


            for item in items_to_refund:


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


                refund_amount += (

                    qty *
                    sell_price

                )



        refund_amount = float(
            refund_amount
        )



        if refund_amount <= 0:


            raise Exception(
                "Refund Amount 0 ဖြစ်နေပါသည်။"
            )







        # ==========================================
        # 4. Insert Refund Record
        # ==========================================

        refund_data = {


            "receipt_no":

                receipt_no,



            "items":

                json.dumps(
                    items_to_refund,
                    ensure_ascii=False
                ),



            "refund_amount":

                refund_amount,



            "refunded_at":

                get_myanmar_time(),



            "status":

                "completed",



            "details":

                f"Refund {len(items_to_refund)} items"

        }



        refund_result = (

            supabase
            .table("refunds")
            .insert(
                refund_data
            )
            .execute()

        )



        if not refund_result.data:


            raise Exception(
                "Refund History သိမ်း၍မရပါ"
            )






        # ==========================================
        # 5. Update Sales Status
        # ==========================================

        update_result = (

            supabase
            .table("sales")
            .update(

                {

                    "status":
                        "refunded"

                }

            )
            .eq(
                "id",
                invoice_id
            )
            .execute()

        )



        if not update_result.data:


            raise Exception(
                "Sales Status Update မအောင်မြင်ပါ"
            )






        return refund_amount





    except Exception as e:


        raise Exception(
            f"Refund Failed : {str(e)}"
        )
