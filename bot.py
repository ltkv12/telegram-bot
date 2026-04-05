import asyncio
import os
import re
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
DB_PATH = "products.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name_ru TEXT NOT NULL,
            name_en TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            expiry TEXT,
            weight TEXT,
            photo TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def save_product_to_db(product):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO products (id, name_ru, name_en, price, stock, expiry, weight, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (product['id'], product['name_ru'], product['name_en'], 
          product['price'], product['stock'], product['expiry'], 
          product['weight'], product['photo']))
    conn.commit()
    conn.close()

def get_stock_from_db(product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_stock_in_db(product_id, new_stock):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    conn.commit()
    conn.close()

def decrease_stock_in_db(product_id, quantity):
    current = get_stock_from_db(product_id)
    if current >= quantity:
        update_stock_in_db(product_id, current - quantity)
        return True
    return False

def load_all_products_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    rows = cursor.fetchall()
    conn.close()
    products = {}
    for row in rows:
        products[row['id']] = dict(row)
    return products

# ========== ID ==========
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
ADMINS_IDS = [int(id.strip()) for id in os.environ.get("ADMINS_IDS", str(OWNER_ID)).split(",") if id.strip()]
ORDERS_CHAT_ID = int(os.environ.get("ORDERS_CHAT_ID", OWNER_ID))
REVIEWS_CHAT_LINK = os.environ.get("REVIEWS_CHAT_LINK", "https://t.me/+xxxxxxxxxxx")

# ========== СОСТОЯНИЯ ==========
class OrderForm(StatesGroup):
    waiting_for_fullname = State()
    waiting_for_username = State()
    waiting_for_phone = State()
    waiting_for_delivery = State()
    waiting_for_pickup_point = State()

class SearchForm(StatesGroup):
    waiting_for_query = State()

class AdminStates(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_edit_choice = State()
    waiting_for_new_price = State()
    waiting_for_new_stock = State()
    waiting_for_new_expiry = State()

# ========== ТОВАРЫ (НАЧАЛЬНЫЕ ДАННЫЕ) ==========
BRAVECTO_TABLETS_PHOTO = "https://raw.githubusercontent.com/ltkv12/telegram-bot/main/images/bravecto_tablets.jpg"
BRAVECTO_DROPS_PHOTO = "https://raw.githubusercontent.com/ltkv12/telegram-bot/main/images/bravecto_drops.jpg"
SIMPARICA_PHOTO = "https://raw.githubusercontent.com/ltkv12/telegram-bot/main/images/simparica.jpg"
SIMPARICA_TRIO_PHOTO = "https://raw.githubusercontent.com/ltkv12/telegram-bot/main/images/simparica%20trio.jpg"
TIXFLI_PHOTO = "https://raw.githubusercontent.com/ltkv12/telegram-bot/main/images/tixfli.jpg"

INITIAL_PRODUCTS = [
    {"id": 1, "name_ru": "Бравекто до 5 кг", "name_en": "Bravecto up to 5 kg", "weight": "до 5 кг", "price": 3400, "expiry": "01.2027", "stock": 10, "photo": BRAVECTO_TABLETS_PHOTO},
    {"id": 2, "name_ru": "Бравекто 5-10 кг", "name_en": "Bravecto 5-10 kg", "weight": "5-10 кг", "price": 3500, "expiry": "05.2027", "stock": 8, "photo": BRAVECTO_TABLETS_PHOTO},
    {"id": 3, "name_ru": "Бравекто 10-20 кг", "name_en": "Bravecto 10-20 kg", "weight": "10-20 кг", "price": 3700, "expiry": "05.2027", "stock": 12, "photo": BRAVECTO_TABLETS_PHOTO},
    {"id": 4, "name_ru": "Бравекто 20-40 кг", "name_en": "Bravecto 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "02.2027", "stock": 6, "photo": BRAVECTO_TABLETS_PHOTO},
    {"id": 5, "name_ru": "Бравекто 40-56 кг", "name_en": "Bravecto 40-56 kg", "weight": "40-56 кг", "price": 4100, "expiry": "02.2027", "stock": 4, "photo": BRAVECTO_TABLETS_PHOTO},
    {"id": 6, "name_ru": "Бравекто капли 5-10 кг", "name_en": "Bravecto drops 5-10 kg", "weight": "5-10 кг", "price": 3700, "expiry": "12.2026", "stock": 7, "photo": BRAVECTO_DROPS_PHOTO},
    {"id": 7, "name_ru": "Бравекто капли 10-20 кг", "name_en": "Bravecto drops 10-20 kg", "weight": "10-20 кг", "price": 3800, "expiry": "12.2026", "stock": 5, "photo": BRAVECTO_DROPS_PHOTO},
    {"id": 8, "name_ru": "Симпарика 1.3-2.5 кг", "name_en": "Simparica 1.3-2.5 kg", "weight": "1.3-2.5 кг", "price": 3300, "expiry": "03.2027", "stock": 8, "photo": SIMPARICA_PHOTO},
    {"id": 9, "name_ru": "Симпарика 2.5-5 кг", "name_en": "Simparica 2.5-5 kg", "weight": "2.5-5 кг", "price": 3500, "expiry": "11.2027", "stock": 10, "photo": SIMPARICA_PHOTO},
    {"id": 10, "name_ru": "Симпарика 5-10 кг", "name_en": "Simparica 5-10 kg", "weight": "5-10 кг", "price": 3600, "expiry": "10.2027", "stock": 12, "photo": SIMPARICA_PHOTO},
    {"id": 11, "name_ru": "Симпарика 10-20 кг", "name_en": "Simparica 10-20 kg", "weight": "10-20 кг", "price": 3800, "expiry": "10.2027", "stock": 9, "photo": SIMPARICA_PHOTO},
    {"id": 12, "name_ru": "Симпарика 20-40 кг", "name_en": "Simparica 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "10.2027", "stock": 7, "photo": SIMPARICA_PHOTO},
    {"id": 13, "name_ru": "Симпарика 40-60 кг", "name_en": "Simparica 40-60 kg", "weight": "40-60 кг", "price": 4000, "expiry": "12.2026", "stock": 5, "photo": SIMPARICA_PHOTO},
    {"id": 14, "name_ru": "Симпарика ТРИО 1.3-2.5 кг", "name_en": "Simparica TRIO 1.3-2.5 kg", "weight": "1.3-2.5 кг", "price": 3300, "expiry": "02.2027", "stock": 6, "photo": SIMPARICA_TRIO_PHOTO},
    {"id": 15, "name_ru": "Симпарика ТРИО 2.5-5 кг", "name_en": "Simparica TRIO 2.5-5 kg", "weight": "2.5-5 кг", "price": 3300, "expiry": "02.2027", "stock": 8, "photo": SIMPARICA_TRIO_PHOTO},
    {"id": 16, "name_ru": "Симпарика ТРИО 5-10 кг", "name_en": "Simparica TRIO 5-10 kg", "weight": "5-10 кг", "price": 3400, "expiry": "12.2026", "stock": 10, "photo": SIMPARICA_TRIO_PHOTO},
    {"id": 17, "name_ru": "Симпарика ТРИО 10-20 кг", "name_en": "Simparica TRIO 10-20 kg", "weight": "10-20 кг", "price": 3600, "expiry": "03.2027", "stock": 7, "photo": SIMPARICA_TRIO_PHOTO},
    {"id": 18, "name_ru": "Симпарика ТРИО 20-40 кг", "name_en": "Simparica TRIO 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "02.2027", "stock": 5, "photo": SIMPARICA_TRIO_PHOTO},
    {"id": 19, "name_ru": "Симпарика ТРИО 40-60 кг", "name_en": "Simparica TRIO 40-60 kg", "weight": "40-60 кг", "price": 4100, "expiry": "02.2027", "stock": 4, "photo": SIMPARICA_TRIO_PHOTO},
    {"id": 20, "name_ru": "Тиксфли 2-4.5 кг", "name_en": "Tixfli 2-4.5 kg", "weight": "2-4.5 кг", "price": 2400, "expiry": "12.2026", "stock": 15, "photo": TIXFLI_PHOTO},
    {"id": 21, "name_ru": "Тиксфли 4.5-10 кг", "name_en": "Tixfli 4.5-10 kg", "weight": "4.5-10 кг", "price": 2500, "expiry": "12.2026", "stock": 12, "photo": TIXFLI_PHOTO},
    {"id": 22, "name_ru": "Тиксфли 10-20 кг", "name_en": "Tixfli 10-20 kg", "weight": "10-20 кг", "price": 2600, "expiry": "12.2026", "stock": 10, "photo": TIXFLI_PHOTO},
    {"id": 23, "name_ru": "Тиксфли 20-40 кг", "name_en": "Tixfli 20-40 kg", "weight": "20-40 кг", "price": 2700, "expiry": "12.2026", "stock": 8, "photo": TIXFLI_PHOTO},
    {"id": 24, "name_ru": "Тиксфли 40-56 кг", "name_en": "Tixfli 40-56 kg", "weight": "40-56 кг", "price": 2900, "expiry": "12.2026", "stock": 6, "photo": TIXFLI_PHOTO},
]

init_db()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
conn.close()

if count == 0:
    for product in INITIAL_PRODUCTS:
        save_product_to_db(product)
    print("✅ Начальные товары сохранены в базу")

ALL_PRODUCTS = load_all_products_from_db()
print(f"✅ Загружено {len(ALL_PRODUCTS)} товаров из базы")

BRAVECTO_TABLETS = [ALL_PRODUCTS[i] for i in range(1, 6)]
BRAVECTO_DROPS = [ALL_PRODUCTS[i] for i in range(6, 8)]
SIMPARICA = [ALL_PRODUCTS[i] for i in range(8, 14)]
SIMPARICA_TRIO = [ALL_PRODUCTS[i] for i in range(14, 20)]
TIXFLI = [ALL_PRODUCTS[i] for i in range(20, 25)]

carts = {}

def is_admin(user_id):
    return user_id in ADMINS_IDS

def get_product(product_id):
    return ALL_PRODUCTS.get(product_id)

def get_product_stock(product_id):
    return get_stock_from_db(product_id)

def update_product_stock(product_id, new_stock):
    update_stock_in_db(product_id, new_stock)
    if product_id in ALL_PRODUCTS:
        ALL_PRODUCTS[product_id]['stock'] = new_stock
    return True

def decrease_stock(product_id, quantity):
    if decrease_stock_in_db(product_id, quantity):
        if product_id in ALL_PRODUCTS:
            ALL_PRODUCTS[product_id]['stock'] -= quantity
        return True
    return False

def update_product_price(product_id, new_price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET price = ? WHERE id = ?', (new_price, product_id))
    conn.commit()
    conn.close()
    if product_id in ALL_PRODUCTS:
        ALL_PRODUCTS[product_id]['price'] = new_price
    return True

def update_product_expiry(product_id, new_expiry):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET expiry = ? WHERE id = ?', (new_expiry, product_id))
    conn.commit()
    conn.close()
    if product_id in ALL_PRODUCTS:
        ALL_PRODUCTS[product_id]['expiry'] = new_expiry
    return True

def validate_phone(phone):
    return re.match(r'^\+7\d{10}$', phone) is not None

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ ЧАСТЫЕ ВОПРОСЫ", callback_data="faq")],
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🔍 ПОИСК", callback_data="search")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="⭐ ОТЗЫВЫ", url=REVIEWS_CHAT_LINK)]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 ВСЕ ТОВАРЫ", callback_data="admin_stock")],
        [InlineKeyboardButton(text="✏️ ИЗМЕНИТЬ ТОВАР", callback_data="admin_edit_stock")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

def edit_choice_menu(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 ИЗМЕНИТЬ ЦЕНУ", callback_data=f"edit_price_{product_id}")],
        [InlineKeyboardButton(text="📦 ИЗМЕНИТЬ ОСТАТКИ", callback_data=f"edit_stock_{product_id}")],
        [InlineKeyboardButton(text="📅 ИЗМЕНИТЬ СРОК ГОДНОСТИ", callback_data=f"edit_expiry_{product_id}")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_back")]
    ])

def catalog_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Бравекто (таблетки)", callback_data="show_bravecto_tablets")],
        [InlineKeyboardButton(text="🟢 Бравекто (капли)", callback_data="show_bravecto_drops")],
        [InlineKeyboardButton(text="🟠 Симпарика", callback_data="show_simparica")],
        [InlineKeyboardButton(text="🟠 Симпарика ТРИО", callback_data="show_simparica_trio")],
        [InlineKeyboardButton(text="🔵 Тиксфли", callback_data="show_tixfli")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

def category_buttons(products):
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"📦 {p['weight']} - {p['price']}₽", callback_data=f"add_{p['id']}")])
    buttons.append([InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")])
    buttons.append([InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def search_result_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Бравекто (таблетки)", callback_data="search_go_bravecto_tablets")],
        [InlineKeyboardButton(text="🟢 Бравекто (капли)", callback_data="search_go_bravecto_drops")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

def cart_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ ОЧИСТИТЬ", callback_data="clear_cart")],
        [InlineKeyboardButton(text="🚚 ОФОРМИТЬ", callback_data="checkout")],
        [InlineKeyboardButton(text="🛍️ ПРОДОЛЖИТЬ", callback_data="catalog")]
    ])

def delivery_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ОЗОН", callback_data="delivery_ozon")],
        [InlineKeyboardButton(text="🚗 САМОВЫВОЗ", callback_data="delivery_samovyvoz")],
        [InlineKeyboardButton(text="🚚 СДЭК", callback_data="delivery_cdek")],
        [InlineKeyboardButton(text="🚛 ЯНДЕКС", callback_data="delivery_yandex")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

def faq_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🔍 ПОИСК", callback_data="search")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

CATEGORIES = {
    "bravecto_tablets": {"name": "🟢 Бравекто (таблетки)", "short_name": "Бравекто таблетки", "desc": "✅ Надежная защита от блох и клещей на 12 недель\n💊 Одна таблетка", "photo": BRAVECTO_TABLETS_PHOTO, "products": BRAVECTO_TABLETS, "keywords": ["бравекто таблетки", "bravecto tablets"]},
    "bravecto_drops": {"name": "🟢 Бравекто (капли)", "short_name": "Бравекто капли", "desc": "✅ Капли от блох и клещей\n💊 Защита на 12 недель", "photo": BRAVECTO_DROPS_PHOTO, "products": BRAVECTO_DROPS, "keywords": ["бравекто капли", "bravecto drops"]},
    "simparica": {"name": "🟠 Симпарика", "short_name": "Симпарика", "desc": "✅ Надежная защита от блох и клещей\n💊 1 таблетка на 30 дней", "photo": SIMPARICA_PHOTO, "products": SIMPARICA, "keywords": ["симпарика", "simparica"]},
    "simparica_trio": {"name": "🟠 Симпарика ТРИО", "short_name": "Симпарика ТРИО", "desc": "✅ Уничтожает блох и клещей\n✅ Предотвращает дирофиляриоз\n✅ Лечит и контролирует круглых и анкилостом\n💊 3 таблетки", "photo": SIMPARICA_TRIO_PHOTO, "products": SIMPARICA_TRIO, "keywords": ["симпарика трио", "simparica trio"]},
    "tixfli": {"name": "🔵 Тиксфли", "short_name": "Тиксфли", "desc": "✅ Защита от блох и клещей", "photo": TIXFLI_PHOTO, "products": TIXFLI, "keywords": ["тиксфли", "tixfli"]}
}

# ========== ОБРАБОТЧИК СТАРТА С КНОПКОЙ ==========
@dp.message(Command("start"))
async def start(message: Message):
    start_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ЗАПУСТИТЬ БОТА", callback_data="start_bot")]
    ])
    
    welcome_text = """🐾 *VetProfil* 

🐾 *Профессиональные решения для здоровья животных* 

✏️ Мы предлагаем ветеринарные препараты и товары от проверенных производителей, которым доверяют специалисты 

⚡️ Внимательно подбираем ассортимент 
⚡️ Контролируем качество 
⚡️ Работаем на результат 

❤️ *Для тех, кто заботится о своих питомцах осознанно* 

✅ *VetProfil — надёжный партнёр в ветеринарии*

👇 *НАЖМИТЕ КНОПКУ ДЛЯ ЗАПУСКА* 👇"""
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=start_button)

@dp.callback_query(F.data == "start_bot")
async def start_bot(call: CallbackQuery):
    await call.message.edit_text(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer("🔧 АДМИН-ПАНЕЛЬ\n\nУправление товарами:", reply_markup=admin_menu())

# ========== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (ПОИСК, КАТАЛОГ, КОРЗИНА, ОФОРМЛЕНИЕ) ==========
# ... (остальной код остаётся без изменений, только функции start заменены)

# ========== ЗАПУСК ==========
async def main():
    print("🚀 Бот VetProfil запущен!")
    print("💾 Остатки сохраняются в базе данных SQLite!")
    print("🔍 Поиск: 'Бравекто' покажет таблетки и капли")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
