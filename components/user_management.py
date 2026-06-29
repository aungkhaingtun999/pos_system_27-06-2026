import streamlit as st

from components.supabase_logic import supabase



# ==========================================
# USER MANAGEMENT
# ==========================================

def show_user_management():

    st.title(
        "👥 User Management"
    )


    # Database Check

    if supabase is None:

        st.error(
            "Supabase Connection မရှိပါ"
        )

        return



    # ======================================
    # ADD USER
    # ======================================

    with st.expander(
        "➕ User အသစ်ထည့်ရန်"
    ):


        with st.form(
            "add_user_form"
        ):


            username = st.text_input(
                "Username"
            )


            password = st.text_input(
                "Password",
                type="password"
            )


            role = st.selectbox(

                "Role",

                [
                    "Admin",
                    "Inventory Manager",
                    "Cashier"
                ]

            )


            submit = st.form_submit_button(
                "Create User"
            )



            if submit:


                if not username or not password:


                    st.warning(
                        "Username နှင့် Password ဖြည့်ပါ"
                    )

                    return



                try:


                    supabase.table(
                        "users"
                    ).insert({

                        "username":username,

                        "password":password,

                        "role":role

                    }).execute()



                    st.success(
                        "User ထည့်ပြီးပါပြီ"
                    )


                    st.rerun()



                except Exception as e:


                    st.error(
                        f"Create User Error : {e}"
                    )




    st.divider()



    # ======================================
    # USER LIST
    # ======================================

    try:


        result=(

            supabase
            .table("users")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()

        )


        users=result.data or []



    except Exception as e:


        st.error(
            f"Load User Error : {e}"
        )

        return





    if not users:


        st.info(
            "User မရှိသေးပါ"
        )

        return






    # ======================================
    # DISPLAY USER
    # ======================================


    for user in users:


        username=user.get(
            "username",
            ""
        )


        role=user.get(
            "role",
            ""
        )


        uid=user.get(
            "id"
        )



        c1,c2,c3=st.columns(
            [3,1,1]
        )



        c1.write(
            f"👤 {username} ({role})"
        )



        if c2.button(

            "🔑 Reset",

            key=f"reset_{uid}"

        ):


            try:

                supabase.table(
                    "users"
                ).update({

                    "password":"123"

                }).eq(

                    "id",
                    uid

                ).execute()



                st.success(
                    "Password Reset = 123"
                )

                st.rerun()


            except Exception as e:

                st.error(e)






        if c3.button(

            "🗑 Delete",

            key=f"delete_{uid}"

        ):



            if username.lower()=="admin":


                st.warning(
                    "Admin ကို ဖျက်၍မရပါ"
                )


            else:


                supabase.table(
                    "users"
                ).delete().eq(

                    "id",
                    uid

                ).execute()


                st.success(
                    "User ဖျက်ပြီးပါပြီ"
                )

                st.rerun()
