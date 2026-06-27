import streamlit as st
from supabase import create_client

# Supabase ချိတ်ဆက်ခြင်း (secrets ထဲတွင် ထည့်ထားရန်လိုအပ်သည်)
# st.secrets["SUPABASE_URL"] နှင့် st.secrets["SUPABASE_KEY"] ကို သေချာစစ်ဆေးပါ
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_user_management():
    st.subheader("👥 User Management (Admin Only)")
    
    # 1. User အသစ်ထည့်ခြင်း
    with st.expander("➕ User အသစ်ထည့်ရန်"):
        with st.form("add_user_form"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Admin", "Inventory Manager", "Cashier"])
            submitted = st.form_submit_button("Create User")
            
            if submitted:
                if new_user and new_pass:
                    try:
                        # Supabase သို့ Data ပေးပို့ခြင်း
                        data = {
                            "username": new_user,
                            "password": new_pass,
                            "role": role
                        }
                        response = supabase.table("users").insert(data).execute()
                        st.success(f"User {new_user} ကို ထည့်သွင်းပြီးပါပြီ။")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: ဖြစ်နိုင်ခြေရှိသော အမှား - {e}")
    
    # 2. လက်ရှိ User များကို ပြသခြင်း
    st.divider()
    st.write("### လက်ရှိ User စာရင်း")
    
    # Supabase မှ Data ဆွဲထုတ်ခြင်း
    response = supabase.table("users").select("*").execute()
    users = response.data
    
    if users:
        for user in users:
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"👤 **{user['username']}** ({user['role']})")
            
            # Password Reset
            if col2.button("Reset Pwd", key=f"reset_{user['id']}"):
                try:
                    supabase.table("users").update({"password": "123"}).eq("id", user['id']).execute()
                    st.success(f"{user['username']} ၏ Password ကို 123 သို့ ပြန်ပြောင်းပြီးပါပြီ။")
                    st.rerun()
                except Exception as e:
                    st.error(f"Reset လုပ်ရာတွင် အမှားဖြစ်သည်: {e}")
            
            # User ဖျက်ရန်
            if col3.button("Delete", key=f"del_{user['id']}"):
                if user['username'] != "admin": 
                    supabase.table("users").delete().eq("id", user['id']).execute()
                    st.rerun()
                else:
                    col3.warning("Admin ကို ဖျက်၍မရပါ။")
    else:
        st.info("User စာရင်း မရှိသေးပါ။")
