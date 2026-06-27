import streamlit as st
from database import get_all_users, reset_password
import sqlite3

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
                        conn = sqlite3.connect("sales.db")
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                                       (new_user, new_pass, role))
                        conn.commit()
                        conn.close()
                        st.success(f"User {new_user} ကို ထည့်သွင်းပြီးပါပြီ။")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: Username ရှိပြီးသားဖြစ်နေနိုင်ပါသည်။ ({e})")
    
    # 2. လက်ရှိ User များကို ပြသပြီး Reset လုပ်ခြင်း
    st.divider()
    st.write("### လက်ရှိ User စာရင်း")
    users = get_all_users() # database.py ထဲက function ကို သုံးသည်
    
    for username, role in users.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.write(f"**{username}** ({role})")
        if col2.button("Reset Password", key=f"reset_{username}"):
            if reset_password(username):
                st.success(f"{username} ၏ Password ကို 123 သို့ ပြန်ပြောင်းပြီးပါပြီ။")
                st.rerun()
        
        # User ဖျက်ရန်
        if col3.button("Delete", key=f"del_{username}"):
            if username != "admin": # admin ကို ဖျက်လို့မရအောင်
                conn = sqlite3.connect("sales.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                conn.close()
                st.rerun()
            else:
                col3.warning("Admin ကို ဖျက်၍မရပါ။")