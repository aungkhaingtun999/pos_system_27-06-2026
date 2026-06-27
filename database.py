import sqlite3
import json
from datetime import datetime, timezone, timedelta

DB_NAME = "sales.db"

# --- Utility Functions ---
def get_myanmar_time():
    return datetime.now(timezone(timedelta(hours=6, minutes=30)))

# --- 1. Database Initialization ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_no TEXT,
            sale_date TEXT,
            items TEXT,
            totals TEXT,
            payment_method TEXT DEFAULT 'Cash',
            customer_name TEXT,
            is_synced INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            product_name TEXT,
            stock_qty INTEGER,
            buy_price REAL,
            sell_price REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', '123'), ('staff1', '123')")
    conn.commit()
    conn.close()

# --- 2. Sales Operations ---
def save_sale(cart, totals, receipt_no=None, payment_method="Cash", customer_name=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        sale_date_str = get_myanmar_time().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO sales (receipt_no, sale_date, items, totals, payment_method, customer_name, is_synced)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (receipt_no, sale_date_str, json.dumps(cart, ensure_ascii=False), json.dumps(totals, ensure_ascii=False), payment_method, customer_name))
        
        for item in cart:
            cart_barcode = str(item.get('barcode', '')).strip()
            qty_sold = int(item.get('qty', 1))
            cursor.execute('''
                UPDATE products SET stock_qty = stock_qty - ? WHERE barcode = ?
            ''', (qty_sold, cart_barcode))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- 3. User Authentication ---
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users")
    users = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return users

def update_password_db(username, new_password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    conn.close()
    return True

def reset_password(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", ("123456", username))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

# --- 4. Report Operations ---
def get_sales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_report_by_date(start_date, end_date):
    """SQLite တွင် ရက်စွဲကို DATE() function ဖြင့် တိကျစွာ filter လုပ်ခြင်း"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # နေ့စွဲကို string format သို့ပြောင်းခြင်း
    s_date = start_date.strftime('%Y-%m-%d')
    e_date = end_date.strftime('%Y-%m-%d')
    
    # sale_date ထဲမှ ရက်စွဲကိုသာ ထုတ်ယူပြီး နှိုင်းယှဉ်ခြင်း (Time ကို လျစ်လျူရှုမည်)
    cursor.execute('''
        SELECT * FROM sales 
        WHERE DATE(sale_date) BETWEEN DATE(?) AND DATE(?) 
        ORDER BY sale_date DESC
    ''', (s_date, e_date))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()