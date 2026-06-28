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


        receipt_no = inv.get(
            "receipt_no"
        )



        # =========================================
        # 1. Check sales status
        # =========================================

        sales_check = (

            supabase
            .table("sales")
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



        if sales_check.data:


            current_status = sales_check.data.get(
                "status"
            )


            if current_status == "refunded":


                raise Exception(
                    "⚠️ ဒီ Receipt ကို Refund လုပ်ပြီးသားဖြစ်ပါသည်။"
                )





        # =========================================
        # 2. Check refund history
        # =========================================

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





        # =========================================
        # 3. Calculate refund
        # =========================================

        if refund_amount is None:


            refund_amount = 0.0


            for item in items_to_refund:


                qty = int(

                    item.get(
                        "qty",
                        1
                    )

                )


                price = safe_float(

                    item.get(
                        "sell_price",
                        0
                    )

                )


                refund_amount += (

                    qty *
                    price

                )






        # =========================================
        # 4. Insert refund history FIRST
        # =========================================

        refund_data = {


            "receipt_no":

                receipt_no,



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



        refund_result = (

            supabase
            .table("refunds")
            .insert(
                refund_data
            )
            .execute()

        )




        # =========================================
        # 5. Update sales status
        # =========================================


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





        return refund_amount





    except Exception as e:


        raise Exception(
            f"Refund Failed : {e}"
        )
