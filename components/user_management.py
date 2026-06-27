import streamlit as st
from supabase import create_client

# Supabase ချိတ်ဆက်ခြင်း
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_user_management():
    st.subheader("👥 User Management (Admin Only)")
    
    # 1. User အသစ်ထည့်ခြင်း
    with st.expander("➕ User အသစ်ထည့်ရန်"):
        with st.form("add_user_form", clear_on_submit=True):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Admin", "Inventory Manager", "Cashier"])
            submitted = st.form_submit_button("Create User")
            
            if submitted:
                if new_user and new_pass:
                    # Supabase သို့ Data ပေးပို့ခြင်း
                    data = {"username": new_user, "password": new_pass, "role": role}
                    try:
                        supabase.table("users").insert(data).execute()
                        st.success(f"User {new_user} ကို ထည့်သွင်းပြီးပါပြီ။")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.divider()
    
    # 2. လက်ရှိ User များကို ပြသခြင်း
    try:
        response = supabase.table("users").select("*").execute()
        users = response.data
        
        if users:
            for user in users:
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"👤 **{user['username']}** ({user['role']})")
                
                # Password Reset (Username ကို သုံး၍)
                if col2.button("Reset Pwd", key=f"reset_{user['username']}"):
                    supabase.table("users").update({"password": "123"}).eq("username", user['username']).execute()
                    st.rerun()
                
                # User ဖျက်ရန် (Username ကို သုံး၍)
                if col3.button("Delete", key=f"del_{user['username']}"):
                    if user['username'] != "admin": 
                        supabase.table("users").delete().eq("username", user['username']).execute()
                        st.rerun()
                    else:
                        col3.warning("Admin ကို ဖျက်၍မရပါ။")
        else:
            st.info("User စာရင်း မရှိသေးပါ။")
    except Exception as e:
        st.error(f"Database မှ Data ဆွဲယူရာတွင် အမှားဖြစ်သည်: {e}")
