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

class AdminStates(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_edit_choice = State()  # Что будем менять: цену, остатки или срок
    waiting_for_new_price = State()
    waiting_for_new_stock = State()
    waiting_for_new_expiry = State()

# ========== ТОВАРЫ ==========
PRODUCTS = {
    "antiparasitic": [
        {"id": 1, "name": "Бравекто 2-4.5 кг", "price": 1850, "desc": "Защита 12 недель\nДля собак 2-4.5 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 5, "expiry": "12.2026"},
        {"id": 2, "name": "Бравекто 4.5-10 кг", "price": 2150, "desc": "Защита 12 недель\nДля собак 4.5-10 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 3, "expiry": "12.2026"},
        {"id": 3, "name": "Бравекто 10-20 кг", "price": 2450, "desc": "Защита 12 недель\nДля собак 10-20 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 7, "expiry": "12.2026"},
        {"id": 4, "name": "Бравекто 20-40 кг", "price": 2850, "desc": "Защита 12 недель\nДля собак 20-40 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 2, "expiry": "12.2026"},
        {"id": 5, "name": "Бравекто 40-56 кг", "price": 3250, "desc": "Защита 12 недель\nДля собак 40-56 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 4, "expiry": "12.2026"},
        {"id": 6, "name": "Нексгард 4-10 кг", "price": 1950, "desc": "Защита 1 месяц\nДля собак 4-10 кг\n3 таблетки", "photo": "https://i.imgur.com/LpQxE6k.jpg", "stock": 8, "expiry": "10.2026"},
        {"id": 7, "name": "Симпарика 5-10 кг", "price": 1850, "desc": "Защита 1 месяц\nДля собак 5-10 кг\n3 таблетки", "photo": "https://i.imgur.com/WK9qP5c.jpg", "stock": 6, "expiry": "10.2026"},
    ],
    "medicine": [
        {"id": 8, "name": "Стоп-зуд", "price": 890, "desc": "Антигистаминный\nОт аллергического зуда\n20 таблеток", "photo": "https://i.imgur.com/8Qk3lB.jpg", "stock": 10, "expiry": "08.2027"},
        {"id": 9, "name": "Энтеросгель", "price": 450, "desc": "Энтеросорбент\nПри отравлениях\n225 г", "photo": "https://i.imgur.com/9Qk3lB.jpg", "stock": 15, "expiry": "05.2027"},
    ],
    "vitamins": [
        {"id": 10, "name": "Глюкозамин", "price": 1250, "desc": "Для суставов\nДля крупных пород\n90 таблеток", "photo": "https://i.imgur.com/glucosamine.jpg", "stock": 12, "expiry": "03.2027"},
        {"id": 11, "name": "Омега-3", "price": 980, "desc": "Для шерсти\nУлучшает состояние\n60 капсул", "photo": "https://i.imgur.com/omega3.jpg", "stock": 20, "expiry": "03.2027"},
    ],
}

carts = {}

def is_admin(user_id):
    return user_id in ADMINS_IDS

def get_product(product_id):
    for cat in PRODUCTS.values():
        for p in cat:
            if p['id'] == product_id:
                return p
    return None

def get_product_stock(product_id):
    product = get_product(product_id)
    return product['stock'] if product else 0

def update_product_price(product_id, new_price):
    product = get_product(product_id)
    if product:
        product['price'] = new_price
        return True
    return False

def update_product_stock(product_id, new_stock):
    product = get_product(product_id)
    if product:
        product['stock'] = new_stock
        return True
    return False

def update_product_expiry(product_id, new_expiry):
    product = get_product(product_id)
    if product:
        product['expiry'] = new_expiry
        return True
    return False

def decrease_stock(product_id, quantity):
    product = get_product(product_id)
    if product and product['stock'] >= quantity:
        product['stock'] -= quantity
        return True
    return False

def get_all_products():
    result = []
    for cat in PRODUCTS.values():
        result.extend(cat)
    return result

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

def categories_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 ОТ БЛОХ И КЛЕЩЕЙ", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 ЛЕКАРСТВА", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 ВИТАМИНЫ", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
    ])

def product_buttons(product_id, stock):
    if stock > 0:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ В КОРЗИНУ", callback_data=f"add_{product_id}")],
            [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
            [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ НЕТ В НАЛИЧИИ", callback_data="no_stock")],
            [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
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

def admin_back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ НАЗАД В АДМИН-ПАНЕЛЬ", callback_data="admin_back")]
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
У СДЭК доступна услуга "наложка" (https://nalozhka.cdek.ru/). Комиссия 5%.

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

# ========== АДМИН: ПРОСМОТР ТОВАРОВ ==========
@dp.callback_query(F.data == "admin_stock")
async def admin_show_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    products = get_all_products()
    text = "📊 *ВСЕ ТОВАРЫ:*\n\n"
    for p in products:
        text += f"🆔 ID: {p['id']}\n"
        text += f"📦 *{p['name']}*\n"
        text += f"   💰 Цена: {p['price']} руб.\n"
        text += f"   📦 Остаток: {p['stock']} шт.\n"
        text += f"   📅 Срок годности: {p.get('expiry', 'Не указан')}\n\n"
    await call.message.answer(text, parse_mode="Markdown", reply_markup=admin_menu())
    await call.message.delete()
    await call.answer()

# ========== АДМИН: ВЫБОР ТОВАРА ДЛЯ ИЗМЕНЕНИЯ ==========
@dp.callback_query(F.data == "admin_edit_stock")
async def admin_edit_stock_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    products = get_all_products()
    text = "✏️ *ВВЕДИТЕ ID ТОВАРА ДЛЯ РЕДАКТИРОВАНИЯ:*\n\n"
    for p in products:
        text += f"🆔 ID: {p['id']} - {p['name']}\n"
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
                f"📦 *{product['name']}*\n\n"
                f"💰 Цена: {product['price']} руб.\n"
                f"📦 Остаток: {product['stock']} шт.\n"
                f"📅 Срок годности: {product.get('expiry', 'Не указан')}\n\n"
                f"✏️ *ЧТО ХОТИТЕ ИЗМЕНИТЬ?*",
                parse_mode="Markdown",
                reply_markup=edit_choice_menu(product_id, product['name'])
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
            f"📦 *{product['name']}*\n"
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
            f"📦 {product['name']}\n"
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
            f"📦 *{product['name']}*\n"
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
            f"📦 {product['name']}\n"
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
            f"📦 *{product['name']}*\n"
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
    
    # Проверяем формат ММ.ГГГГ
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
        f"📦 {product['name']}\n"
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
    await call.message.answer("📁 ВЫБЕРИТЕ КАТЕГОРИЮ:", reply_markup=categories_menu())
    await call.message.delete()
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_products(call: CallbackQuery):
    category = call.data.split("_")[1]
    products = PRODUCTS.get(category, [])
    if not products:
        await call.message.answer("😕 Товаров нет")
        await call.message.delete()
        await call.answer()
        return
    
    await call.message.answer("📦 ТОВАРЫ:")
    await call.message.delete()
    
    is_admin_user = is_admin(call.from_user.id)
    
    for product in products:
        stock = product['stock']
        expiry = product.get('expiry', 'Не указан')
        
        text = f"*{product['name']}*\n\n"
        text += f"{product['desc']}\n\n"
        text += f"💰 *Цена: {product['price']} руб.*\n"
        text += f"📅 *Срок годности:* {expiry}\n"
        
        if is_admin_user:
            if stock > 0:
                text += f"📦 *В наличии: {stock} шт.*"
            else:
                text += f"❌ *НЕТ В НАЛИЧИИ*"
        
        try:
            await call.message.answer_photo(photo=product['photo'], caption=text, parse_mode="Markdown", reply_markup=product_buttons(product['id'], stock))
        except:
            await call.message.answer(text, parse_mode="Markdown", reply_markup=product_buttons(product['id'], stock))
    await call.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    product = get_product(product_id)
    if not product:
        await call.answer("❌ Товар не найден")
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
        carts[user_id][product_id] = {'name': product['name'], 'price': product['price'], 'qty': 1}
    
    await call.answer(f"✅ {product['name']}\nВ корзине: {carts[user_id][product_id]['qty']} шт.", show_alert=True)

@dp.callback_query(F.data == "no_stock")
async def no_stock_handler(call: CallbackQuery):
    await call.answer("❌ Нет в наличии", show_alert=True)

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
    text = "🛒 ВАША КОРЗИНА\n\n"
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"{item['name']}\n   {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
        total_items += item['qty']
    text += f"ИТОГО: {total_items} шт.\nСУММА: {total} руб."
    await call.message.answer(text, reply_markup=cart_buttons())
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
        current_stock = get_product_stock(int(product_id))
        if item['qty'] > current_stock:
            await message.answer(f"❌ Невозможно оформить заказ!\n{item['name']} - в наличии {current_stock} шт.")
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
    order_text += f
