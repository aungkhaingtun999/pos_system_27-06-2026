import streamlit as st
import socket
import sys
import os

# --- Import Path Fix (Root Directory ရှာဖွေခြင်း) ---
# sidebar.py သည် components folder ထဲတွင်ရှိနေသဖြင့် အပြင်ဘက်သို့ တစ်ဆင့်ထွက်ရန် dirname နှစ်ခါသုံးထားသည်
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- Imports ---
from auth import logout, change_password
from language import get_text
# အဟောင်း (Error ဖြစ်စေသောနေရာ)
# from components.supabase_logic import sync_to_supabase

# အသစ် (ဤသို့ ပြင်ဆင်ပါ)
# components/sidebar.py ၏ 20-line ဝန်းကျင်ကို ဤသို့ပြင်ပါ
from .supabase_logic import sync_to_supabase
# ==========================================
# Helper Functions
# ==========================================
def _check_internet():
    """အင်တာနက် ချိတ်ဆက်မှု စစ်ဆေးခြင်း"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def _handle_menu_change(selected_menu):
    """Menu ပြောင်းလဲသောအခါ Session နှင့် URL ပြောင်းလဲခြင်း"""
    st.session_state.menu = selected_menu
    st.query_params["menu"] = selected_menu
    st.rerun()

# ==========================================
# Main Sidebar UI
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
            # Language ရွေးချယ်မှု
            lang = st.selectbox("🌐", lang_options, index=lang_options.index(current_lang), label_visibility="collapsed")
            if lang != current_lang:
                st.session_state.lang = lang
                st.rerun()
        
        st.markdown("---")
        
        # 2. User Info (Role Banner ဖယ်ရှားပြီး သန့်ရှင်းစွာပြသခြင်း)
        username = st.session_state.get('username', 'User')
        role = st.session_state.get("user_role", "Cashier")
        st.info(f"👤 **{username}**\n\n🛡️ Role: *{role}*")
        
        # 3. Sync Data (Logic)
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
        # အကယ်၍ Role ပြောင်းသွားပြီး menu မရှိတော့လျှင် POS System သို့ ပြန်သွားပါ
        if current_menu not in menu_items:
            current_menu = "POS System"
            st.session_state.menu = "POS System"
        
        # Radio Menu
        selected_menu = st.radio(
            "📌 Main Menu", 
            menu_items, 
            index=menu_items.index(current_menu),
            key="main_menu_radio"
        )
        
        if selected_menu != current_menu:
            _handle_menu_change(selected_menu)
        
        st.markdown("---")
        
        # 5. Account Settings & Logout
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True): 
            st.session_state.show_pwd_change = True
            
        # Password Change UI (Container ထဲတွင် ထည့်ထားခြင်းဖြင့် နေရာမလုတော့ပါ)
        if st.session_state.get("show_pwd_change", False):
            with st.container(border=True):
                change_password()
                if st.button("❌ Close", key="cls_pwd", use_container_width=True): 
                    st.session_state.show_pwd_change = False
                    st.rerun()
        
        # Logout
        if st.button("🚪 Log Out", key="out_btn", use_container_width=True): 
            logout()
