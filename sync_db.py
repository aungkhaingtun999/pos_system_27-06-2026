# ==========================================
# 1. Imports
# ==========================================
import sqlite3
import json
from supabase_logic import insert_sale_to_supabase

# ==========================================
# 2. Helper Functions (Connection)
# ==========================================
DB_NAME = "sales.db"

def _get_db_connection():
    """SQLite Database connection ကို ထုတ်ပေးခြင်း"""
    return sqlite3.connect(DB_NAME)

# ==========================================
# 3. Main Run Modules (Sync Operations)
# ==========================================
def sync_old_data_to_supabase():
    """SQLite မှ Data များကို Supabase သို့ Sync လုပ်ပေးသော Main module"""
    print("Sync စတင်နေပါပြီ...")
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT receipt_no, items, totals, payment_method, customer_name FROM sales")
        rows = cursor.fetchall()
        
        count = 0
        for row in rows:
            receipt_no, items_json, totals_json, payment, customer = row
            try:
                # JSON Data များကို Unicode ပံ့ပိုးမှုဖြင့် ပြန်လည်ဖတ်ယူခြင်း
                cart = json.loads(items_json)
                totals = json.loads(totals_json)
                
                # Supabase ထဲသို့ ပို့ဆောင်ခြင်း
                if insert_sale_to_supabase(cart, totals, receipt_no, payment, customer):
                    count += 1
            except Exception as e:
                print(f"Error processing receipt {receipt_no}: {e}")
        
        print(f"Sync ပြီးပါပြီ။ စုစုပေါင်း {count} ခု ပို့ဆောင်ပြီးပါပြီ။")
        
    except sqlite3.Error as e:
        print(f"Database error during sync: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sync_old_data_to_supabase()