# ==========================================
# 1. Imports
# ==========================================
import sqlite3
import os

# ==========================================
# 2. Helper Functions (Configuration)
# ==========================================
def get_db_path():
    """Database ဖိုင်တည်နေရာကို သတ်မှတ်ပေးခြင်း"""
    return r"C:\Users\aungkhaingtun\Desktop\Offline_onLine_GPT_apps -\sales.db"

def get_db_connection():
    """Database connection ပြုလုပ်ပေးခြင်း"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Error: '{db_path}' ဖိုင်ကို မတွေ့ရှိပါ။")
    return sqlite3.connect(db_path)

# ==========================================
# 3. Main Run Modules (Operations)
# ==========================================
def get_all_barcodes():
    """Database ထဲမှ Barcode များအားလုံးကို ဆွဲထုတ်ခြင်း"""
    barcodes = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT barcode FROM products")
            # Database မှရလာသော data များကို list အဖြစ်ပြောင်းပြီး trim လုပ်ခြင်း
            barcodes = [str(row[0]).strip() for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error while fetching barcodes: {e}")
    
    return barcodes

def display_database_info():
    """Database ထဲတွင်ရှိသော Table များနှင့် Barcode များကို ပြသခြင်း"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Table များစစ်ဆေးခြင်း
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Database ထဲမှာရှိတဲ့ Table များ: {tables}")
            
            # Barcode များထုတ်ယူခြင်း
            barcodes = get_all_barcodes()
            print(f"Database ထဲမှာရှိတဲ့ Barcode များ: {barcodes}")
            
    except Exception as e:
        print(f"Database error: {e}")

# ==========================================
# Main Execution
# ==========================================
if __name__ ==