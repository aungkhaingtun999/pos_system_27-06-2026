# ==========================================
# 1. Imports
# ==========================================
import streamlit as st

# ==========================================
# 2. Helper Functions (Configuration Constants)
# ==========================================
def get_supabase_config():
    """Supabase configuration များကို လုံခြုံစွာထုတ်ယူခြင်း"""
    return {
        "url": st.secrets.get("SUPABASE_URL", ""),
        "key": st.secrets.get("SUPABASE_KEY", "")
    }

def get_db_settings():
    """Local SQLite Database ဆိုင်ရာ Settings များ"""
    return {
        "db_name": "sales.db",
        "backup_folder": "backups"
    }

def get_app_settings():
    """App ဆိုင်ရာ အခြေခံ settings များ"""
    return {
        "app_name": "Barcode POS System",
        "currency": "MMK",
        "decimal_places": 2,
        "encoding": "utf-8",
        "low_stock_threshold": 5, # Low Stock Alert အတွက် default တန်ဖိုး
        "tax_rate_default": 0.0
    }

# ==========================================
# 3. Run Module (Initialization)
# ==========================================
def init_session():
    """Application အတွက် လိုအပ်သော Session State များကို စတင်ခြင်း"""
    
    # POS Cart
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    # User Session
    if "username" not in st.session_state:
        st.session_state.username = None
    
    # Language ကို Default အနေဖြင့် 'EN' (English) ဟု သတ်မှတ်ပေးခြင်း
    if "lang" not in st.session_state:
        st.session_state.lang = "EN"
        
    # UI/System States
    if "settings" not in st.session_state:
        st.session_state.settings = get_app_settings()
        
    if "db_settings" not in st.session_state:
        st.session_state.db_settings = get_db_settings()

    if "show_pwd_change" not in st.session_state:
        st.session_state.show_pwd_change = False
        
    if "menu" not in st.session_state:
        st.session_state.menu = "POS System"

# ==========================================
# 4. Global Configuration Access
# ==========================================
# Application တစ်ခုလုံးတွင် အသုံးပြုရန် Constants များ
SUPABASE_CONFIG = get_supabase_config()
APP_SETTINGS = get_app_settings()
DB_SETTINGS = get_db_settings()

# မှတ်ချက် -
# ဤဖိုင်ကို အသုံးပြုရန် မည်သည့် Module မှမဆို 
# `from config import SUPABASE_CONFIG, APP_SETTINGS, DB_SETTINGS` 
# ဟု အလွယ်တကူ ခေါ်ယူအသုံးပြုနိုင်ပါသည်။