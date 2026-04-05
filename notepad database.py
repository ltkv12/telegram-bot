import sqlite3
import os

DB_PATH = "products.db"

def init_db():
    """Создаёт таблицу с товарами, если её нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            expiry TEXT,
            weight TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def get_stock(product_id):
    """Получить остаток товара по ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_stock(product_id, new_stock):
    """Обновить остаток товара"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    conn.commit()
    conn.close()
    return True

def decrease_stock(product_id, quantity):
    """Уменьшить остаток товара"""
    current = get_stock(product_id)
    if current >= quantity:
        update_stock(product_id, current - quantity)
        return True
    return False

def save_all_products(products_dict):
    """Сохраняет все товары в базу (один раз при запуске)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for product_id, product in products_dict.items():
        cursor.execute('''
            INSERT OR REPLACE INTO products (id, name, price, stock, expiry, weight)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            product.get('name', ''),
            product.get('price', 0),
            product.get('stock', 0),
            product.get('expiry', ''),
            product.get('weight', '')
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Сохранено {len(products_dict)} товаров в базу")

def load_stocks_to_memory(products_dict):
    """Загружает остатки из базы в память при запуске"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, stock FROM products')
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        product_id, stock = row
        if product_id in products_dict:
            products_dict[product_id]['stock'] = stock
    
    print("✅ Остатки загружены из базы")
