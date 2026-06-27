import streamlit as st
import socket
from auth import logout, change_password
from language import get_text 

# ==========================================
# 2. Helper Functions (Connection & Navigation)
# ==========================================
def _check_internet():
    """အင်တာနက် ချိတ်ဆက်မှု ရှိမရှိ စစ်ဆေးခြင်း"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def _handle_menu_change(selected_menu):
    """Menu ပြောင်းလဲမှုကို စီမံခန့်ခွဲခြင်း"""
    st.session_state.menu = selected_menu
    # st.query_params သည် Streamlit version အသစ်များအတွက်သုံးပါ
    st.query_params["menu"] = selected_menu
    st.rerun()

# ==========================================
# 3. Main Run Module (Sidebar UI)
# ==========================================
def show_sidebar():
    """Sidebar UI ကို Render လုပ်ပေးသော Main module"""
    with st.sidebar:
        # Internet Status
        if _check_internet():
            st.success(get_text("Online", st.session_state.get("lang")))
        else:
            st.error(get_text("Offline", st.session_state.get("lang")))

        # Language Switcher
        lang_options = ["MY", "EN"]
        current_lang = st.session_state.get("lang", "MY")
        lang = st.selectbox("🌐 Language", lang_options, index=lang_options.index(current_lang))
        if lang != current_lang:
            st.session_state.lang = lang
            st.rerun()
            
        # User Info & Role
        role = st.session_state.get("user_role", "Cashier")
        username = st.session_state.get('username', 'User')
        st.write(f"👤 User: **{username}**")
        st.caption(f"🛡️ Role: {role}")
        
        # Sync Data
        if st.button("🔄 Sync Data Now", key="sync_btn", use_container_width=True):
            if _check_internet():
                from components.supabase_logic import sync_to_supabase # Path မှန်အောင်ပြင်ထားပါ
                with st.spinner("Syncing..."):
                    sync_to_supabase()
                st.success("✅ Success")
            else:
                st.warning("⚠️ No Internet Connection")
        
        st.markdown("---")
        
        # --- Role-Based Menu Logic ---
        menu_items = ["POS System"]
        
        # Admin သို့မဟုတ် Inventory Manager ဖြစ်မှသာ Inventory မြင်ရမည်
        if role in ["Admin", "Inventory Manager"]:
            menu_items.append("Inventory")
            
        # Admin သာလျှင် Reports နှင့် Profit & Loss ကို မြင်ရမည်
        if role == "Admin":
            menu_items.extend(["Reports", "Profit & Loss", "User Management"]) # User Management ထည့်ထားသည်
            
        menu_items.append("Refund")
        
        # လက်ရှိ menu ကို သတ်မှတ်ခြင်း
        current_menu = st.session_state.get("menu", "POS System")
        
        # မရှိတော့တဲ့ Menu တစ်ခုခုမှာ ရောက်နေရင် POS သို့ပြန်ပို့ပေးခြင်း
        if current_menu not in menu_items:
            current_menu = "POS System"
            st.session_state.menu = "POS System"
        
        selected_menu = st.radio(
            "📌 Main Menu", 
            menu_items, 
            index=menu_items.index(current_menu)
        )
        
        if selected_menu != current_menu:
            _handle_menu_change(selected_menu)
        
        st.markdown("---")
        
        # Password & Logout
        if st.button("🔑 Change Password", key="chg_pwd", use_container_width=True): 
            st.session_state.show_pwd_change = True
            
        if st.session_state.get("show_pwd_change", False):
            change_password()
            if st.button("❌ Close Password", key="cls_pwd"): 
                st.session_state.show_pwd_change = False
                st.rerun()
        
        if st.button("🚪 Log Out", key="out_btn", use_container_width=True): 
            logout()
