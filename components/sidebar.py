import streamlit as st
import socket
from auth import logout, change_password
from language import get_text 

# ==========================================
# 2. Helper Functions (Connection & Navigation)
# ==========================================
def _check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def _handle_menu_change(selected_menu):
    st.session_state.menu = selected_menu
    st.query_params["menu"] = selected_menu
    st.rerun()

# ==========================================
# 3. Main Run Module (Sidebar UI)
# ==========================================
def show_sidebar():
    with st.sidebar:
        # 1. Status Section (Internet & Language)
        col1, col2 = st.columns([1, 1])
        with col1:
            if _check_internet():
                st.success("🟢 Online")
            else:
                st.error("🔴 Offline")
        with col2:
            lang_options = ["MY", "EN"]
            current_lang = st.session_state.get("lang", "MY")
            lang = st.selectbox("🌐", lang_options, index=lang_options.index(current_lang), label_visibility="collapsed")
            if lang != current_lang:
                st.session_state.lang = lang
                st.rerun()
        
        st.markdown("---")
        
        # 2. User Profile (Banner များကို ဖယ်ရှားပြီး သန့်ရှင်းစွာပြသခြင်း)
        username = st.session_state.get('username', 'User')
        role = st.session_state.get("user_role", "Cashier")
        st.info(f"👤 **{username}**\n\n🛡️ Role: *{role}*")
        
        # 3. Quick Action (Sync Data)
        if st.button("🔄 Sync Data Now", key="sync_btn", use_container_width=True):
            if _check_internet():
                from components.supabase_logic import sync_to_supabase
                with st.spinner("Syncing..."):
                    sync_to_supabase()
                st.success("✅ Success")
            else:
                st.warning("⚠️ No Internet Connection")
        
        st.markdown("---")
        
        # 4. Role-Based Menu Logic
        menu_items = ["POS System"]
        if role in ["Admin", "Inventory Manager"]:
            menu_items.append("Inventory")
        if role == "Admin":
            menu_items.extend(["Reports", "Profit & Loss", "User Management"])
        menu_items.append("Refund")
        
        current_menu = st.session_state.get("menu", "POS System")
        if current_menu not in menu_items:
            current_menu = "POS System"
            st.session_state.menu = "POS System"
        
        menu_index = menu_items.index(current_menu)
        
        selected_menu = st.radio(
            "📌 Main Menu", 
            menu_items, 
            index=menu_index,
            key="main_menu_radio"
        )
        
        if selected_menu != current_menu:
            _handle_menu_change(selected_menu)
        
        st.markdown("---")
        
        # 5. Account Settings & Logout
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True): 
            st.session_state.show_pwd_change = True
            
        if st.session_state.get("show_pwd_change", False):
            # Password ပြောင်းခြင်းလုပ်ဆောင်ချက်ကို Box တစ်ခုအတွင်း ထည့်ပေးထားသည်
            with st.container(border=True):
                change_password()
                if st.button("❌ Close", key="cls_pwd", use_container_width=True): 
                    st.session_state.show_pwd_change = False
                    st.rerun()
        
        st.write("") # နေရာအနည်းငယ်ချန်ရန်
        if st.button("🚪 Log Out", key="out_btn", use_container_width=True): 
            logout()
