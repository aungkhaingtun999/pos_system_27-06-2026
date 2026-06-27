import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta

# Cloud တွင် /tmp folder ကိုသာ write လုပ်ခွင့်ရှိသဖြင့် ၎င်းကို သုံးခြင်း
DB_NAME = "/tmp/sales.db"

def get_myanmar_time():
    return datetime.now(timezone(timedelta(hours=6, minutes=30)))

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tables creation
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_no TEXT, sale_date TEXT, items TEXT, totals TEXT, payment_method TEXT DEFAULT 'Cash', customer_name TEXT, is_synced INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (barcode TEXT PRIMARY KEY, product_name TEXT, stock_qty INTEGER, buy_price REAL, sell_price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT DEFAULT 'Cashier')''')
    
    # Default Admin & Staff
    try:
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', '123', 'Admin'), ('staff1', '123', 'Cashier')")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

# --- Authentication ---
def get_user_from_db(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
    row = cursor.fetchone()
    conn.close()
    return {"username": row[0], "role": row[1]} if row else None

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    users = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return users

def update_password_db(username, old_pass, new_pass):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ? AND password = ?", (new_pass, username, old_pass))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def reset_password(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", ("123", username))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

# --- Sales Operations ---
def save_sale(cart, totals, receipt_no=None, payment_method="Cash", customer_name=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        sale_date_str = get_myanmar_time().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO sales (receipt_no, sale_date, items, totals, payment_method, customer_name, is_synced) VALUES (?, ?, ?, ?, ?, ?, 0)', 
                       (receipt_no, sale_date_str, json.dumps(cart, ensure_ascii=False), json.dumps(totals, ensure_ascii=False), payment_method, customer_name))
        
        for item in cart:
            cursor.execute('UPDATE products SET stock_qty = stock_qty - ? WHERE barcode = ?', (int(item.get('qty', 1)), str(item.get('barcode', '')).strip()))
        conn.commit()
    finally:
        conn.close()

# --- Report Operations ---
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
    cursor.execute('SELECT * FROM sales WHERE DATE(sale_date) BETWEEN DATE(?) AND DATE(?) ORDER BY sale_date DESC', 
                   (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    rows = cursor.fetchall()
    conn.close()
    return rows

# App စတင်ချိန်တွင် Database ကို အသင့်ပြင်ဆင်ခြင်း
init_db()
