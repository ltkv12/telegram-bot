import asyncio
import os
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

# ========== ТОВАРЫ ==========
BRAVECTO_TABLETS = [
    {"id": 1, "name_ru": "Бравекто до 5 кг", "name_en": "Bravecto up to 5 kg", "weight": "до 5 кг", "price": 3400, "expiry": "01.2027", "stock": 10, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    {"id": 2, "name_ru": "Бравекто 5-10 кг", "name_en": "Bravecto 5-10 kg", "weight": "5-10 кг", "price": 3500, "expiry": "05.2027", "stock": 8, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    {"id": 3, "name_ru": "Бравекто 10-20 кг", "name_en": "Bravecto 10-20 kg", "weight": "10-20 кг", "price": 3700, "expiry": "05.2027", "stock": 12, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    {"id": 4, "name_ru": "Бравекто 20-40 кг", "name_en": "Bravecto 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "02.2027", "stock": 6, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    {"id": 5, "name_ru": "Бравекто 40-56 кг", "name_en": "Bravecto 40-56 kg", "weight": "40-56 кг", "price": 4100, "expiry": "02.2027", "stock": 4, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
]

BRAVECTO_DROPS = [
    {"id": 6, "name_ru": "Бравекто капли 5-10 кг", "name_en": "Bravecto drops 5-10 kg", "weight": "5-10 кг", "price": 3700, "expiry": "12.2026", "stock": 7, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    {"id": 7, "name_ru": "Бравекто капли 10-20 кг", "name_en": "Bravecto drops 10-20 kg", "weight": "10-20 кг", "price": 3800, "expiry": "12.2026", "stock": 5, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
]

SIMPARICA = [
    {"id": 8, "name_ru": "Симпарика 1.3-2.5 кг", "name_en": "Simparica 1.3-2.5 kg", "weight": "1.3-2.5 кг", "price": 3300, "expiry": "03.2027", "stock": 8, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 9, "name_ru": "Симпарика 2.5-5 кг", "name_en": "Simparica 2.5-5 kg", "weight": "2.5-5 кг", "price": 3500, "expiry": "11.2027", "stock": 10, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 10, "name_ru": "Симпарика 5-10 кг", "name_en": "Simparica 5-10 kg", "weight": "5-10 кг", "price": 3600, "expiry": "10.2027", "stock": 12, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 11, "name_ru": "Симпарика 10-20 кг", "name_en": "Simparica 10-20 kg", "weight": "10-20 кг", "price": 3800, "expiry": "10.2027", "stock": 9, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 12, "name_ru": "Симпарика 20-40 кг", "name_en": "Simparica 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "10.2027", "stock": 7, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 13, "name_ru": "Симпарика 40-60 кг", "name_en": "Simparica 40-60 kg", "weight": "40-60 кг", "price": 4000, "expiry": "12.2026", "stock": 5, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
]

SIMPARICA_TRIO = [
    {"id": 14, "name_ru": "Симпарика ТРИО 1.3-2.5 кг", "name_en": "Simparica TRIO 1.3-2.5 kg", "weight": "1.3-2.5 кг", "price": 3300, "expiry": "02.2027", "stock": 6, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 15, "name_ru": "Симпарика ТРИО 2.5-5 кг", "name_en": "Simparica TRIO 2.5-5 kg", "weight": "2.5-5 кг", "price": 3300, "expiry": "02.2027", "stock": 8, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 16, "name_ru": "Симпарика ТРИО 5-10 кг", "name_en": "Simparica TRIO 5-10 kg", "weight": "5-10 кг", "price": 3400, "expiry": "12.2026", "stock": 10, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 17, "name_ru": "Симпарика ТРИО 10-20 кг", "name_en": "Simparica TRIO 10-20 kg", "weight": "10-20 кг", "price": 3600, "expiry": "03.2027", "stock": 7, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 18, "name_ru": "Симпарика ТРИО 20-40 кг", "name_en": "Simparica TRIO 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "02.2027", "stock": 5, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    {"id": 19, "name_ru": "Симпарика ТРИО 40-60 кг", "name_en": "Simparica TRIO 40-60 kg", "weight": "40-60 кг", "price": 4100, "expiry": "02.2027", "stock": 4, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
]

TIXFLI = [
    {"id": 20, "name_ru": "Тиксфли 2-4.5 кг", "name_en": "Tixfli 2-4.5 kg", "weight": "2-4.5 кг", "price": 2400, "expiry": "12.2026", "stock": 15, "photo": "https://i.imgur.com/8Qk3lB.jpg"},
    {"id": 21, "name_ru": "Тиксфли 4.5-10 кг", "name_en": "Tixfli 4.5-10 kg", "weight": "4.5-10 кг", "price": 2500, "expiry": "12.2026", "stock": 12, "photo": "https://i.imgur.com/8Qk3lB.jpg"},
    {"id": 22, "name_ru": "Тиксфли 10-20 кг", "name_en": "Tixfli 10-20 kg", "weight": "10-20 кг", "price": 2600, "expiry": "12.2026", "stock": 10, "photo": "https://i.imgur.com/8Qk3lB.jpg"},
    {"id": 23, "name_ru": "Тиксфли 20-40 кг", "name_en": "Tixfli 20-40 kg", "weight": "20-40 кг", "price": 2700, "expiry": "12.2026", "stock": 8, "photo": "https://i.imgur.com/8Qk3lB.jpg"},
    {"id": 24, "name_ru": "Тиксфли 40-56 кг", "name_en": "Tixfli 40-56 kg", "weight": "40-56 кг", "price": 2900, "expiry": "12.2026", "stock": 6, "photo": "https://i.imgur.com/8Qk3lB.jpg"},
]

# Словари для категорий
CATEGORIES = {
    "bravecto_tablets": {"name": "Бравекто (таблетки)", "products": BRAVECTO_TABLETS, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    "bravecto_drops": {"name": "Бравекто (капли)", "products": BRAVECTO_DROPS, "photo": "https://i.imgur.com/5Q8k3lB.jpg"},
    "simparica": {"name": "Симпарика", "products": SIMPARICA, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    "simparica_trio": {"name": "Симпарика ТРИО", "products": SIMPARICA_TRIO, "photo": "https://i.imgur.com/WK9qP5c.jpg"},
    "tixfli": {"name": "Тиксфли", "products": TIXFLI, "photo": "https://i.imgur.com/8Qk3lB.jpg"},
}

# Общий словарь всех товаров по ID
ALL_PRODUCTS = {}
for cat in CATEGORIES.values():
    for product in cat["products"]:
        ALL_PRODUCTS[product["id"]] = product

carts = {}
current_search_category = {}

def is_admin(user_id):
    return user_id in ADMINS_IDS

def get_product(product_id):
    return ALL_PRODUCTS.get(product_id)

def search_in_category(query, category_products):
    """Поиск товара в конкретной категории"""
    query_lower = query.lower().strip()
    results = []
    for product in category_products:
        if query_lower in product["name_ru"].lower() or query_lower in product["name_en"].lower():
            results.append(product)
    return results

def update_product_price(product_id, new_price):
    if product_id in ALL_PRODUCTS:
        ALL_PRODUCTS[product_id]['price'] = new_price
        return True
    return False

def update_product_stock(product_id, new_stock):
    if product_id in ALL_PRODUCTS:
        ALL_PRODUCTS[product_id]['stock'] = new_stock
        return True
    return False

def update_product_expiry(product_id, new_expiry):
    if product_id in ALL_PRODUCTS:
        ALL_PRODUCTS[product_id]['expiry'] = new_expiry
        return True
    return False

def decrease_stock(product_id, quantity):
    if product_id in ALL_PRODUCTS and ALL_PRODUCTS[product_id]['stock'] >= quantity:
        ALL_PRODUCTS[product_id]['stock'] -= quantity
        return True
    return False

def validate_phone(phone):
    return re.match(r'^\+7\d{10}$', phone) is not None

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ ЧАСТЫЕ ВОПРОСЫ", callback_data="faq")],
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="⭐ ОТЗЫВЫ", url=REVIEWS_CHAT_LINK)]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 ВСЕ ТОВАРЫ", callback_data="admin_stock")],
        [InlineKeyboardButton(text="✏️ ИЗМЕНИТЬ ТОВАР", callback_data="admin_edit_stock")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

def edit_choice_menu(product_id, product_name):
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

def category_action_buttons(category_key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 ПОИСК В КАТЕГОРИИ", callback_data=f"search_in_{category_key}")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")]
    ])

def product_buttons(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ В КОРЗИНУ", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")]
    ])

def search_result_buttons(product_id, category_key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ ДОБАВИТЬ В КОРЗИНУ", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="🔍 НОВЫЙ ПОИСК", callback_data=f"search_in_{category_key}")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")]
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
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

# ========== ПРИВЕТСТВИЕ ==========
@dp.message(Command("start"))
async def start(message: Message):
    welcome_text = """🐾 *VetProfil* 

🐾 *Профессиональные решения для здоровья животных* 

✏️ Мы предлагаем ветеринарные препараты и товары от проверенных производителей, которым доверяют специалисты 

⚡️ Внимательно подбираем ассортимент 
⚡️ Контролируем качество 
⚡️ Работаем на результат 

❤️ *Для тех, кто заботится о своих питомцах осознанно* 

✅ *VetProfil — надёжный партнёр в ветеринарии*

👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇"""
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer("🔧 АДМИН-ПАНЕЛЬ\n\nУправление товарами:", reply_markup=admin_menu())

# ========== ЧАСТЫЕ ВОПРОСЫ ==========
@dp.callback_query(F.data == "faq")
async def faq(call: CallbackQuery):
    faq_text = """❓ *ЧАСТЫЕ ВОПРОСЫ*

📍 *Самовывоз*
Самовывоз возможен в Москве в районе ВАО (адрес уточняйте после согласования заказа и времени самовывоза). Оплата наличными.

📩 *Доставка в другие регионы*
Осуществляется в пункты выдачи заказов (ПВЗ) Яндекс/СДЭК/Озон

💰 *Оплата*
100% перед отправкой, на юр счёт, через безопасную сделку Озон или СДЭК "наложка"

🗣 *Доставка оплачивается отдельно*
• СДЭК - при получении
• Яндекс - вместе с заказом

📍 *Рассчитать стоимость:*
• СДЭК: https://www.cdek.ru/ru/cabinet/calculate/
• Яндекс: в приложении Яндекс Go

⭕️ *Риски*

🗣 *Доставка Яндекс*
Дешевле, но последнее время стали часто терять посылки. В случае утери выяснение информации - ваша зона ответственности.

🗣 *Доставка СДЭК*
Дороже, но все посылки застрахованы. Упаковка надежнее.

🗣 *Наложка*
У СДЭК доступна услуга "наложка". Комиссия 5%.

🚚 *Отправление заказов происходит ежедневно*

⏰ *Обработка заказов: с 9:00 до 16:00 (МСК)*

📌 *ОФОРМЛЕНИЕ ЗАКАЗА*

1️⃣ Название препарата/количество
2️⃣ Город и адрес ПВЗ (с указанием транспортной компании)
3️⃣ ФИО
4️⃣ Телефон

👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇"""
    
    await call.message.edit_text(faq_text, parse_mode="Markdown", reply_markup=faq_menu())
    await call.answer()

# ========== АДМИН: ПРОСМОТР ВСЕХ ТОВАРОВ ==========
@dp.callback_query(F.data == "admin_stock")
async def admin_show_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    
    text = "📊 *ВСЕ ТОВАРЫ:*\n\n"
    for cat_key, cat_data in CATEGORIES.items():
        text += f"📁 *{cat_data['name']}*\n"
        for p in cat_data["products"]:
            text += f"   🆔 ID: {p['id']} - {p['name_ru']} / {p['name_en']} - {p['price']}₽ (в наличии: {p['stock']})\n"
        text += "\n"
    
    await call.message.answer(text, parse_mode="Markdown", reply_markup=admin_menu())
    await call.message.delete()
    await call.answer()

# ========== АДМИН: ВЫБОР ТОВАРА ДЛЯ ИЗМЕНЕНИЯ ==========
@dp.callback_query(F.data == "admin_edit_stock")
async def admin_edit_stock_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    
    text = "✏️ *ВВЕДИТЕ ID ТОВАРА ДЛЯ РЕДАКТИРОВАНИЯ:*\n\n"
    for cat_key, cat_data in CATEGORIES.items():
        text += f"📁 {cat_data['name']}: "
        ids = [str(p['id']) for p in cat_data["products"]]
        text += ", ".join(ids) + "\n"
    
    await call.message.answer(text, parse_mode="Markdown")
    await call.message.delete()
    await state.set_state(AdminStates.waiting_for_product_id)
    await call.answer()

@dp.message(AdminStates.waiting_for_product_id)
async def admin_get_product_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        product_id = int(message.text)
        product = get_product(product_id)
        if product:
            await state.update_data(product_id=product_id)
            await message.answer(
                f"📦 *{product['name_ru']} / {product['name_en']}*\n\n"
                f"💰 Цена: {product['price']} руб.\n"
                f"📦 Остаток: {product['stock']} шт.\n"
                f"📅 Срок годности: {product.get('expiry', 'Не указан')}\n\n"
                f"✏️ *ЧТО ХОТИТЕ ИЗМЕНИТЬ?*",
                parse_mode="Markdown",
                reply_markup=edit_choice_menu(product_id, product['name_ru'])
            )
            await state.clear()
        else:
            await message.answer("❌ Товар не найден. Попробуйте еще раз:")
    except ValueError:
        await message.answer("❌ Введите число (ID товара)")

# ========== АДМИН: ИЗМЕНЕНИЕ ЦЕНЫ ==========
@dp.callback_query(F.data.startswith("edit_price_"))
async def admin_edit_price(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    product_id = int(call.data.split("_")[2])
    product = get_product(product_id)
    if product:
        await state.update_data(product_id=product_id)
        await call.message.answer(
            f"📦 *{product['name_ru']} / {product['name_en']}*\n"
            f"💰 Текущая цена: {product['price']} руб.\n\n"
            f"✏️ *ВВЕДИТЕ НОВУЮ ЦЕНУ (только число):*",
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_new_price)
    await call.answer()

@dp.message(AdminStates.waiting_for_new_price)
async def admin_set_new_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        new_price = int(message.text)
        if new_price <= 0:
            await message.answer("❌ Цена должна быть больше 0!")
            return
        data = await state.get_data()
        product_id = data['product_id']
        update_product_price(product_id, new_price)
        product = get_product(product_id)
        await message.answer(
            f"✅ *ЦЕНА ОБНОВЛЕНА!*\n\n"
            f"📦 {product['name_ru']} / {product['name_en']}\n"
            f"💰 Новая цена: {new_price} руб.",
            parse_mode="Markdown",
            reply_markup=admin_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число (цену в рублях)")

# ========== АДМИН: ИЗМЕНЕНИЕ ОСТАТКОВ ==========
@dp.callback_query(F.data.startswith("edit_stock_"))
async def admin_edit_stock(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    product_id = int(call.data.split("_")[2])
    product = get_product(product_id)
    if product:
        await state.update_data(product_id=product_id)
        await call.message.answer(
            f"📦 *{product['name_ru']} / {product['name_en']}*\n"
            f"📦 Текущий остаток: {product['stock']} шт.\n\n"
            f"✏️ *ВВЕДИТЕ НОВЫЙ ОСТАТОК (число):*",
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_new_stock)
    await call.answer()

@dp.message(AdminStates.waiting_for_new_stock)
async def admin_set_new_stock(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        new_stock = int(message.text)
        if new_stock < 0:
            await message.answer("❌ Остаток не может быть отрицательным!")
            return
        data = await state.get_data()
        product_id = data['product_id']
        update_product_stock(product_id, new_stock)
        product = get_product(product_id)
        await message.answer(
            f"✅ *ОСТАТКИ ОБНОВЛЕНЫ!*\n\n"
            f"📦 {product['name_ru']} / {product['name_en']}\n"
            f"📦 Новый остаток: {new_stock} шт.",
            parse_mode="Markdown",
            reply_markup=admin_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число (количество товара)")

# ========== АДМИН: ИЗМЕНЕНИЕ СРОКА ГОДНОСТИ ==========
@dp.callback_query(F.data.startswith("edit_expiry_"))
async def admin_edit_expiry(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    product_id = int(call.data.split("_")[2])
    product = get_product(product_id)
    if product:
        await state.update_data(product_id=product_id)
        await call.message.answer(
            f"📦 *{product['name_ru']} / {product['name_en']}*\n"
            f"📅 Текущий срок годности: {product.get('expiry', 'Не указан')}\n\n"
            f"✏️ *ВВЕДИТЕ НОВЫЙ СРОК ГОДНОСТИ*\n"
            f"В формате: ММ.ГГГГ\n"
            f"Например: 12.2026",
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_new_expiry)
    await call.answer()

@dp.message(AdminStates.waiting_for_new_expiry)
async def admin_set_new_expiry(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    new_expiry = message.text.strip()
    
    if not re.match(r'^(0[1-9]|1[0-2])\.(20[2-9][0-9])$', new_expiry):
        await message.answer(
            "❌ *НЕВЕРНЫЙ ФОРМАТ!*\n\n"
            "Введите дату в формате: ММ.ГГГГ\n"
            "Например: 12.2026",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    product_id = data['product_id']
    update_product_expiry(product_id, new_expiry)
    product = get_product(product_id)
    
    await message.answer(
        f"✅ *СРОК ГОДНОСТИ ОБНОВЛЁН!*\n\n"
        f"📦 {product['name_ru']} / {product['name_en']}\n"
        f"📅 Новый срок годности: {new_expiry}",
        parse_mode="Markdown",
        reply_markup=admin_menu()
    )
    await state.clear()

# ========== АДМИН: НАЗАД ==========
@dp.callback_query(F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    await call.message.answer("🔧 АДМИН-ПАНЕЛЬ\n\nУправление товарами:", reply_markup=admin_menu())
    await call.message.delete()
    await call.answer()

# ========== КАТАЛОГ ==========
@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    await call.message.answer("📁 *ВЫБЕРИТЕ КАТЕГОРИЮ:*", parse_mode="Markdown", reply_markup=catalog_menu())
    await call.message.delete()
    await call.answer()

# ========== ПОКАЗ КАТЕГОРИИ ==========
def make_category_show_handler(category_key, category_data):
    async def handler(call: CallbackQuery):
        text = f"*{category_data['name']}*\n\n"
        text += f"📊 *Доступные варианты:*\n"
        
        for p in category_data["products"]:
            text += f"• {p['weight']} - {p['price']}₽ (годен до {p['expiry']})\n"
        
        text += "\n👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇"
        
        try:
            await call.message.answer_photo(
                photo=category_data['photo'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=category_action_buttons(category_key)
            )
        except:
            await call.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=category_action_buttons(category_key)
            )
        await call.answer()
    return handler

# Регистрируем обработчики для каждой категории
dp.callback_query(F.data == "show_bravecto_tablets")(make_category_show_handler("bravecto_tablets", CATEGORIES["bravecto_tablets"]))
dp.callback_query(F.data == "show_bravecto_drops")(make_category_show_handler("bravecto_drops", CATEGORIES["bravecto_drops"]))
dp.callback_query(F.data == "show_simparica")(make_category_show_handler("simparica", CATEGORIES["simparica"]))
dp.callback_query(F.data == "show_simparica_trio")(make_category_show_handler("simparica_trio", CATEGORIES["simparica_trio"]))
dp.callback_query(F.data == "show_tixfli")(make_category_show_handler("tixfli", CATEGORIES["tixfli"]))

# ========== ПОИСК В КАТЕГОРИИ ==========
@dp.callback_query(F.data.startswith("search_in_"))
async def search_in_category_start(call: CallbackQuery, state: FSMContext):
    category_key = call.data.split("_")[2]
    current_search_category[call.from_user.id] = category_key
    
    await call.message.edit_text(
        f"🔍 *ПОИСК В КАТЕГОРИИ:* {CATEGORIES[category_key]['name']}\n\n"
        f"Введите название товара на русском или английском языке.\n\n"
        f"Примеры:\n"
        f"• Бравекто / Bravecto\n"
        f"• 5-10 кг\n\n"
        f"🔎 Введите запрос:",
        parse_mode="Markdown"
    )
    await state.set_state(SearchForm.waiting_for_query)
    await call.answer()

@dp.message(SearchForm.waiting_for_query)
async def search_in_category_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    category_key = current_search_category.get(user_id)
    
    if not category_key or category_key not in CATEGORIES:
        await message.answer("❌ Ошибка: категория не выбрана. Пожалуйста, начните поиск заново из каталога.")
        await state.clear()
        return
    
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Введите минимум 2 символа для поиска")
        return
    
    category_data = CATEGORIES[category_key]
    results = search_in_category(query, category_data["products"])
    
    if not results:
        await message.answer(
            f"🔍 По запросу *{query}* в категории *{category_data['name']}* ничего не найдено.\n\n"
            f"Попробуйте другие ключевые слова.",
            parse_mode="Markdown",
            reply_markup=category_action_buttons(category_key)
        )
        await state.clear()
        return
    
    # Отправляем результаты поиска
    await message.answer(f"🔍 *Результаты поиска в категории {category_data['name']} по запросу:* \"{query}\"\n\n📦 Найдено товаров: {len(results)}", parse_mode="Markdown")
    
    for product in results:
        text = f"*{product['name_ru']}* / *{product['name_en']}*\n\n"
        text += f"⚖️ Вес: {product['weight']}\n"
        text += f"💰 Цена: {product['price']}₽\n"
        text += f"📅 Срок годности: {product['expiry']}\n\n"
        text += f"👇 *Добавьте товар в корзину* 👇"
        
        try:
            await message.answer_photo(
                photo=product['photo'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=search_result_buttons(product['id'], category_key)
            )
        except Exception as e:
            await message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=search_result_buttons(product['id'], category_key)
            )
    
    await state.clear()

# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    product = get_product(product_id)
    
    if not product:
        await call.answer(f"❌ Товар не найден", show_alert=True)
        return
    
    user_id = call.from_user.id
    current_in_cart = carts.get(user_id, {}).get(product_id, {}).get('qty', 0)
    
    if current_in_cart >= product['stock']:
        await call.answer(f"❌ НЕЛЬЗЯ! В наличии: {product['stock']} шт.", show_alert=True)
        return
    
    if user_id not in carts:
        carts[user_id] = {}
    if product_id in carts[user_id]:
        carts[user_id][product_id]['qty'] += 1
    else:
        carts[user_id][product_id] = {
            'name': product['name_ru'],
            'price': product['price'],
            'qty': 1,
            'expiry': product['expiry']
        }
    
    await call.answer(f"✅ {product['name_ru']}\nВ корзине: {carts[user_id][product_id]['qty']} шт.", show_alert=True)

# ========== КОРЗИНА ==========
@dp.callback_query(F.data == "show_cart")
async def view_cart(call: CallbackQuery):
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    if not cart:
        await call.message.answer("🛒 КОРЗИНА ПУСТА", reply_markup=main_menu())
        await call.message.delete()
        await call.answer()
        return
    total = 0
    total_items = 0
    text = "🛒 *ВАША КОРЗИНА*\n\n"
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"📦 {item['name']}\n   {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
        total_items += item['qty']
    text += f"📦 *ИТОГО:* {total_items} шт.\n💰 *СУММА:* {total} руб."
    await call.message.answer(text, parse_mode="Markdown", reply_markup=cart_buttons())
    await call.message.delete()
    await call.answer()

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    carts[call.from_user.id] = {}
    await call.message.answer("🗑️ КОРЗИНА ОЧИЩЕНА", reply_markup=main_menu())
    await call.message.delete()
    await call.answer()

# ========== ОФОРМЛЕНИЕ ==========
@dp.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery, state: FSMContext):
    if not carts.get(call.from_user.id):
        await call.answer("Корзина пуста!", show_alert=True)
        return
    await call.message.answer("📝 ОФОРМЛЕНИЕ ЗАКАЗА\n\nШаг 1 из 5\n\n✏️ ВВЕДИТЕ ВАШЕ ПОЛНОЕ ФИО:\n\nНапример: Иванов Иван Иванович")
    await call.message.delete()
    await state.set_state(OrderForm.waiting_for_fullname)
    await call.answer()

@dp.message(OrderForm.waiting_for_fullname)
async def get_fullname(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("❌ Введите корректное ФИО (минимум 5 символов):")
        return
    await state.update_data(fullname=message.text.strip())
    await message.answer("📝 ОФОРМЛЕНИЕ ЗАКАЗА\n\nШаг 2 из 5\n\n🔹 ВВЕДИТЕ ВАШ USERNAME В TELEGRAM:\n\nВ формате: @username\n\nЕсли нет username, введите 'Нет'")
    await state.set_state(OrderForm.waiting_for_username)

@dp.message(OrderForm.waiting_for_username)
async def get_username(message: Message, state: FSMContext):
    username = message.text.strip()
    if username.startswith("@"):
        username = username[1:]
    if username.lower() == "нет":
        username = "Не указан"
    await state.update_data(username=username)
    await message.answer("📝 ОФОРМЛЕНИЕ ЗАКАЗА\n\nШаг 3 из 5\n\n📱 ВВЕДИТЕ НОМЕР ТЕЛЕФОНА:\n\nФормат: +7XXXXXXXXXX\nПример: +79001234567")
    await state.set_state(OrderForm.waiting_for_phone)

@dp.message(OrderForm.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer("❌ НЕВЕРНЫЙ ФОРМАТ!\n\nВведите номер в формате +7XXXXXXXXXX")
        return
    await state.update_data(phone=message.text)
    await message.answer("📝 ОФОРМЛЕНИЕ ЗАКАЗА\n\nШаг 4 из 5\n\n🚚 ВЫБЕРИТЕ СЛУЖБУ ДОСТАВКИ:", reply_markup=delivery_menu())
    await state.set_state(OrderForm.waiting_for_delivery)

@dp.callback_query(OrderForm.waiting_for_delivery, F.data.startswith("delivery_"))
async def select_delivery(call: CallbackQuery, state: FSMContext):
    service = call.data.split("_")[1]
    if service == "samovyvoz":
        service = "САМОВЫВОЗ"
    await state.update_data(delivery=service)
    await call.message.answer("📝 ОФОРМЛЕНИЕ ЗАКАЗА\n\nШаг 5 из 5 (последний)\n\n🏠 УКАЖИТЕ АДРЕС ПУНКТА ВЫДАЧИ,\nгде вам удобно забрать заказ:\n\nНапример: г. Москва, м. Первомайская, ул. Первомайская, д. 1")
    await call.message.delete()
    await state.set_state(OrderForm.waiting_for_pickup_point)
    await call.answer()

@dp.message(OrderForm.waiting_for_pickup_point)
async def get_pickup_point(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    cart = carts.get(user_id, {})
    
    username = data.get('username', 'Не указан')
    
    if not cart:
        await message.answer("❌ Корзина пуста", reply_markup=main_menu())
        await state.clear()
        return
    
    # Проверяем остатки
    for product_id, item in cart.items():
        product = get_product(int(product_id))
        if product and item['qty'] > product['stock']:
            await message.answer(f"❌ Невозможно оформить заказ!\n{item['name']} - в наличии {product['stock']} шт.")
            await state.clear()
            return
    
    # Уменьшаем остатки
    for product_id, item in cart.items():
        decrease_stock(int(product_id), item['qty'])
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    total_items = sum(item['qty'] for item in cart.values())
    
    # Формируем заказ
    order_text = f"✅ НОВЫЙ ЗАКАЗ!\n\n"
    order_text += f"👤 ФИО: {data['fullname']}\n"
    order_text += f"🔹 Username: @{username}\n"
    order_text += f"📱 Телефон: {data['phone']}\n"
    order_text += f"🆔 ID: {user_id}\n"
    order_text += f"🚚 Служба: {data['delivery'].upper()}\n"
    order_text += f"🏠 Пункт выдачи: {message.text}\n\n"
    order_text += f"📦 ТОВАРЫ:\n"
    
    for item in cart.values():
        order_text += f"• {item['name']} x{item['qty']} = {item['price'] * item['qty']} руб.\n"
    
    order_text += f"\n💰 ИТОГО: {total} руб.\n"
    order_text += f"📦 ВСЕГО ТОВАРОВ: {total_items} шт."
    
    # Отправляем заказ в чат
    try:
        await bot.send_message(chat_id=ORDERS_CHAT_ID, text=order_text)
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # Очищаем корзину
    carts[user_id] = {}
    await state.clear()
    
    await message.answer(
        f"✅ ЗАКАЗ ОФОРМЛЕН!\n\n"
        f"👤 {data['fullname']}\n"
        f"🔹 @{username}\n"
        f"📱 {data['phone']}\n"
        f"🚚 {data['delivery'].upper()}\n"
        f"🏠 {message.text}\n"
        f"💰 {total} руб.\n\n"
        f"В ближайшее время с Вами свяжутся для согласования заказа.\n\n"
        f"🐕 Спасибо за покупку!\n\n"
        f"⭐ Оставьте отзыв в разделе 'ОТЗЫВЫ'",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "main_back")
async def main_back(call: CallbackQuery):
    welcome_text = """🐾 *VetProfil* 

🐾 *Профессиональные решения для здоровья животных* 

✏️ Мы предлагаем ветеринарные препараты и товары от проверенных производителей, которым доверяют специалисты 

⚡️ Внимательно подбираем ассортимент 
⚡️ Контролируем качество 
⚡️ Работаем на результат 

❤️ *Для тех, кто заботится о своих питомцах осознанно* 

✅ *VetProfil — надёжный партнёр в ветеринарии*

👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇"""
    
    await call.message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())
    await call.message.delete()
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    print(f"📦 Загружено категорий: {len(CATEGORIES)}")
    print(f"📦 Загружено товаров: {len(ALL_PRODUCTS)}")
    print("🔍 Поиск работает внутри каждой категории")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
