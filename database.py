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
    
    # Sales Table
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
    
    # Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            product_name TEXT,
            stock_qty INTEGER,
            buy_price REAL,
            sell_price REAL
        )
    ''')
    
    # Users Table (Role ပါဝင်သည်)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT DEFAULT 'Cashier'
        )
    ''')
    
    # Default Admin & Staff
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', '123', 'Admin'), ('staff1', '123', 'Cashier')")
    
    conn.commit()
    conn.close()

# --- 2. User Authentication & Role Management ---
def get_user_from_db(username, password):
    """Login ဝင်ချိန်တွင် User နှင့် Role ကို စစ်ဆေးခြင်း"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "role": row[1]}
    return None

def get_all_users():
    """အသုံးပြုသူအားလုံးစာရင်း (Admin အတွက်)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    users = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return users

def update_password_db(username, old_pass, new_pass):
    """Password အဟောင်းမှန်မှသာ အသစ်ပြောင်းခြင်း"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ? AND password = ?", (new_pass, username, old_pass))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def reset_password(username):
    """Admin အနေဖြင့် Password ကို 123 သို့ Reset လုပ်ခြင်း"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", ("123", username))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

# --- 3. Sales Operations ---
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

# --- 4. Report & Inventory Operations ---
def get_sales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_report_by_date(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    s_date = start_date.strftime('%Y-%m-%d')
    e_date = end_date.strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT * FROM sales 
        WHERE DATE(sale_date) BETWEEN DATE(?) AND DATE(?) 
        ORDER BY sale_date DESC
    ''', (s_date, e_date))
    rows = cursor.fetchall()
    conn.close()
    return rows

# App စတင်ချိန်တွင် Database ကို အသင့်ပြင်ဆင်ခြင်း
init_db()
