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
    waiting_for_edit_choice = State()
    waiting_for_new_price = State()
    waiting_for_new_stock = State()
    waiting_for_new_expiry = State()

# ========== ТОВАРЫ (ПРЯМОЕ ОПРЕДЕЛЕНИЕ) ==========
# Бравекто таблетки
BRAVECTO_TABLETS = [
    {"id": 1, "name": "Bravecto up to 5 kg", "weight": "до 5 кг", "price": 3400, "expiry": "01.2027", "stock": 10},
    {"id": 2, "name": "Bravecto 5-10 kg", "weight": "5-10 кг", "price": 3500, "expiry": "05.2027", "stock": 8},
    {"id": 3, "name": "Bravecto 10-20 kg", "weight": "10-20 кг", "price": 3700, "expiry": "05.2027", "stock": 12},
    {"id": 4, "name": "Bravecto 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "02.2027", "stock": 6},
    {"id": 5, "name": "Bravecto 40-56 kg", "weight": "40-56 кг", "price": 4100, "expiry": "02.2027", "stock": 4},
]

# Бравекто капли
BRAVECTO_DROPS = [
    {"id": 6, "name": "Бравекто капли 5-10 кг", "weight": "5-10 кг", "price": 3700, "expiry": "12.2026", "stock": 7},
    {"id": 7, "name": "Бравекто капли 10-20 кг", "weight": "10-20 кг", "price": 3800, "expiry": "12.2026", "stock": 5},
]

# Симпарика
SIMPARICA = [
    {"id": 8, "name": "Simparica 1.3-2.5 kg", "weight": "1.3-2.5 кг", "price": 3300, "expiry": "03.2027", "stock": 8},
    {"id": 9, "name": "Simparica 2.5-5 kg", "weight": "2.5-5 кг", "price": 3500, "expiry": "11.2027", "stock": 10},
    {"id": 10, "name": "Simparica 5-10 kg", "weight": "5-10 кг", "price": 3600, "expiry": "10.2027", "stock": 12},
    {"id": 11, "name": "Simparica 10-20 kg", "weight": "10-20 кг", "price": 3800, "expiry": "10.2027", "stock": 9},
    {"id": 12, "name": "Simparica 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "10.2027", "stock": 7},
    {"id": 13, "name": "Simparica 40-60 kg", "weight": "40-60 кг", "price": 4000, "expiry": "12.2026", "stock": 5},
]

# Симпарика ТРИО
SIMPARICA_TRIO = [
    {"id": 14, "name": "Simparica TRIO 1.3-2.5 kg", "weight": "1.3-2.5 кг", "price": 3300, "expiry": "02.2027", "stock": 6},
    {"id": 15, "name": "Simparica TRIO 2.5-5 kg", "weight": "2.5-5 кг", "price": 3300, "expiry": "02.2027", "stock": 8},
    {"id": 16, "name": "Simparica TRIO 5-10 kg", "weight": "5-10 кг", "price": 3400, "expiry": "12.2026", "stock": 10},
    {"id": 17, "name": "Simparica TRIO 10-20 kg", "weight": "10-20 кг", "price": 3600, "expiry": "03.2027", "stock": 7},
    {"id": 18, "name": "Simparica TRIO 20-40 kg", "weight": "20-40 кг", "price": 3900, "expiry": "02.2027", "stock": 5},
    {"id": 19, "name": "Simparica TRIO 40-60 kg", "weight": "40-60 кг", "price": 4100, "expiry": "02.2027", "stock": 4},
]

# Тиксфли
TIXFLI = [
    {"id": 20, "name": "Тиксфли 2-4.5 кг", "weight": "2-4.5 кг", "price": 2400, "expiry": "12.2026", "stock": 15},
    {"id": 21, "name": "Тиксфли 4.5-10 кг", "weight": "4.5-10 кг", "price": 2500, "expiry": "12.2026", "stock": 12},
    {"id": 22, "name": "Тиксфли 10-20 кг", "weight": "10-20 кг", "price": 2600, "expiry": "12.2026", "stock": 10},
    {"id": 23, "name": "Тиксфли 20-40 кг", "weight": "20-40 кг", "price": 2700, "expiry": "12.2026", "stock": 8},
    {"id": 24, "name": "Тиксфли 40-56 кг", "weight": "40-56 кг", "price": 2900, "expiry": "12.2026", "stock": 6},
]

# ОБЩИЙ СЛОВАРЬ ВСЕХ ТОВАРОВ
ALL_VARIANTS = {}
for item in BRAVECTO_TABLETS + BRAVECTO_DROPS + SIMPARICA + SIMPARICA_TRIO + TIXFLI:
    ALL_VARIANTS[item["id"]] = item

# ГРУППЫ ТОВАРОВ ДЛЯ КАТАЛОГА
PRODUCT_GROUPS = {
    "bravecto_tablets": {
        "name": "🟢 Бравекто (таблетки)",
        "desc": "✅ Надежная защита от блох и клещей на 12 недель\n💊 Одна таблетка",
        "photo": "https://i.imgur.com/5Q8k3lB.jpg",
        "variants": BRAVECTO_TABLETS
    },
    "bravecto_drops": {
        "name": "🟢 Бравекто (капли)",
        "desc": "✅ Капли от блох и клещей\n💊 Защита на 12 недель",
        "photo": "https://i.imgur.com/5Q8k3lB.jpg",
        "variants": BRAVECTO_DROPS
    },
    "simparica": {
        "name": "🟠 Симпарика",
        "desc": "✅ Надежная защита от блох и клещей\n💊 1 таблетка на 30 дней",
        "photo": "https://i.imgur.com/WK9qP5c.jpg",
        "variants": SIMPARICA
    },
    "simparica_trio": {
        "name": "🟠 Симпарика ТРИО",
        "desc": "✅ Уничтожает блох и клещей\n✅ Предотвращает дирофиляриоз\n✅ Лечит и контролирует круглых и анкилостом\n💊 3 таблетки",
        "photo": "https://i.imgur.com/WK9qP5c.jpg",
        "variants": SIMPARICA_TRIO
    },
    "tixfli": {
        "name": "🔵 Тиксфли",
        "desc": "✅ Защита от блох и клещей",
        "photo": "https://i.imgur.com/8Qk3lB.jpg",
        "variants": TIXFLI
    }
}

carts = {}

def is_admin(user_id):
    return user_id in ADMINS_IDS

def get_variant(variant_id):
    return ALL_VARIANTS.get(variant_id)

def get_product_stock(variant_id):
    variant = get_variant(variant_id)
    return variant['stock'] if variant else 0

def update_variant_price(variant_id, new_price):
    variant = get_variant(variant_id)
    if variant:
        variant['price'] = new_price
        return True
    return False

def update_variant_stock(variant_id, new_stock):
    variant = get_variant(variant_id)
    if variant:
        variant['stock'] = new_stock
        return True
    return False

def update_variant_expiry(variant_id, new_expiry):
    variant = get_variant(variant_id)
    if variant:
        variant['expiry'] = new_expiry
        return True
    return False

def decrease_stock(variant_id, quantity):
    variant = get_variant(variant_id)
    if variant and variant['stock'] >= quantity:
        variant['stock'] -= quantity
        return True
    return False

def get_all_variants():
    return list(ALL_VARIANTS.values())

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

def edit_choice_menu(variant_id, variant_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 ИЗМЕНИТЬ ЦЕНУ", callback_data=f"edit_price_{variant_id}")],
        [InlineKeyboardButton(text="📦 ИЗМЕНИТЬ ОСТАТКИ", callback_data=f"edit_stock_{variant_id}")],
        [InlineKeyboardButton(text="📅 ИЗМЕНИТЬ СРОК ГОДНОСТИ", callback_data=f"edit_expiry_{variant_id}")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="admin_back")]
    ])

def catalog_menu():
    buttons = []
    for key, group in PRODUCT_GROUPS.items():
        buttons.append([InlineKeyboardButton(text=group['name'], callback_data=f"product_{key}")])
    buttons.append([InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")])
    buttons.append([InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def variant_buttons(variants):
    buttons = []
    for variant in variants:
        weight = variant['weight']
        price = variant['price']
        buttons.append([InlineKeyboardButton(text=f"📦 {weight} - {price}₽", callback_data=f"add_{variant['id']}")])
    buttons.append([InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")])
    buttons.append([InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

# ========== АДМИН: ПРОСМОТР ТОВАРОВ ==========
@dp.callback_query(F.data == "admin_stock")
async def admin_show_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    variants = get_all_variants()
    text = "📊 *ВСЕ ТОВАРЫ:*\n\n"
    for v in variants:
        text += f"🆔 ID: {v['id']}\n"
        text += f"📦 *{v['name']}*\n"
        text += f"   💰 Цена: {v['price']} руб.\n"
        text += f"   📦 Остаток: {v['stock']} шт.\n"
        text += f"   📅 Срок годности: {v.get('expiry', 'Не указан')}\n\n"
    await call.message.answer(text, parse_mode="Markdown", reply_markup=admin_menu())
    await call.message.delete()
    await call.answer()

# ========== АДМИН: ВЫБОР ТОВАРА ДЛЯ ИЗМЕНЕНИЯ ==========
@dp.callback_query(F.data == "admin_edit_stock")
async def admin_edit_stock_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    variants = get_all_variants()
    text = "✏️ *ВВЕДИТЕ ID ТОВАРА ДЛЯ РЕДАКТИРОВАНИЯ:*\n\n"
    for v in variants:
        text += f"🆔 ID: {v['id']} - {v['name']}\n"
    await call.message.answer(text, parse_mode="Markdown")
    await call.message.delete()
    await state.set_state(AdminStates.waiting_for_product_id)
    await call.answer()

@dp.message(AdminStates.waiting_for_product_id)
async def admin_get_product_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        variant_id = int(message.text)
        variant = get_variant(variant_id)
        if variant:
            await state.update_data(variant_id=variant_id)
            await message.answer(
                f"📦 *{variant['name']}*\n\n"
                f"💰 Цена: {variant['price']} руб.\n"
                f"📦 Остаток: {variant['stock']} шт.\n"
                f"📅 Срок годности: {variant.get('expiry', 'Не указан')}\n\n"
                f"✏️ *ЧТО ХОТИТЕ ИЗМЕНИТЬ?*",
                parse_mode="Markdown",
                reply_markup=edit_choice_menu(variant_id, variant['name'])
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
    variant_id = int(call.data.split("_")[2])
    variant = get_variant(variant_id)
    if variant:
        await state.update_data(variant_id=variant_id)
        await call.message.answer(
            f"📦 *{variant['name']}*\n"
            f"💰 Текущая цена: {variant['price']} руб.\n\n"
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
        variant_id = data['variant_id']
        update_variant_price(variant_id, new_price)
        variant = get_variant(variant_id)
        await message.answer(
            f"✅ *ЦЕНА ОБНОВЛЕНА!*\n\n"
            f"📦 {variant['name']}\n"
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
    variant_id = int(call.data.split("_")[2])
    variant = get_variant(variant_id)
    if variant:
        await state.update_data(variant_id=variant_id)
        await call.message.answer(
            f"📦 *{variant['name']}*\n"
            f"📦 Текущий остаток: {variant['stock']} шт.\n\n"
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
        variant_id = data['variant_id']
        update_variant_stock(variant_id, new_stock)
        variant = get_variant(variant_id)
        await message.answer(
            f"✅ *ОСТАТКИ ОБНОВЛЕНЫ!*\n\n"
            f"📦 {variant['name']}\n"
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
    variant_id = int(call.data.split("_")[2])
    variant = get_variant(variant_id)
    if variant:
        await state.update_data(variant_id=variant_id)
        await call.message.answer(
            f"📦 *{variant['name']}*\n"
            f"📅 Текущий срок годности: {variant.get('expiry', 'Не указан')}\n\n"
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
    variant_id = data['variant_id']
    update_variant_expiry(variant_id, new_expiry)
    variant = get_variant(variant_id)
    
    await message.answer(
        f"✅ *СРОК ГОДНОСТИ ОБНОВЛЁН!*\n\n"
        f"📦 {variant['name']}\n"
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
    await call.message.answer("📁 *ВЫБЕРИТЕ ТОВАР:*", parse_mode="Markdown", reply_markup=catalog_menu())
    await call.message.delete()
    await call.answer()

# ========== ПОКАЗ ТОВАРА С ВАРИАНТАМИ ВЕСА ==========
@dp.callback_query(F.data.startswith("product_"))
async def show_product(call: CallbackQuery):
    product_key = call.data.split("_")[1]
    product_group = PRODUCT_GROUPS.get(product_key)
    
    if not product_group:
        await call.message.answer("😕 Товар не найден")
        return
    
    text = f"*{product_group['name']}*\n\n"
    text += f"{product_group['desc']}\n\n"
    text += "*📊 Доступные варианты:*\n"
    
    for variant in product_group['variants']:
        text += f"• {variant['name']} - {variant['price']}₽ (годен до {variant['expiry']})\n"
    
    text += "\n👇 *ВЫБЕРИТЕ НУЖНЫЙ ВЕС* 👇"
    
    try:
        await call.message.answer_photo(
            photo=product_group['photo'],
            caption=text,
            parse_mode="Markdown",
            reply_markup=variant_buttons(product_group['variants'])
        )
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        await call.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=variant_buttons(product_group['variants'])
        )
    await call.answer()

# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    variant_id = int(call.data.split("_")[1])
    variant = get_variant(variant_id)
    
    if not variant:
        await call.answer(f"❌ Товар с ID {variant_id} не найден", show_alert=True)
        return
    
    user_id = call.from_user.id
    current_in_cart = carts.get(user_id, {}).get(variant_id, {}).get('qty', 0)
    
    if current_in_cart >= variant['stock']:
        await call.answer(f"❌ НЕЛЬЗЯ! В наличии: {variant['stock']} шт.", show_alert=True)
        return
    
    if user_id not in carts:
        carts[user_id] = {}
    if variant_id in carts[user_id]:
        carts[user_id][variant_id]['qty'] += 1
    else:
        carts[user_id][variant_id] = {
            'name': variant['name'],
            'price': variant['price'],
            'qty': 1,
            'expiry': variant['expiry']
        }
    
    await call.answer(f"✅ {variant['name']}\nВ корзине: {carts[user_id][variant_id]['qty']} шт.", show_alert=True)

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
    for variant_id, item in cart.items():
        current_stock = get_product_stock(int(variant_id))
        if item['qty'] > current_stock:
            await message.answer(f"❌ Невозможно оформить заказ!\n{item['name']} - в наличии {current_stock} шт.")
            await state.clear()
            return
    
    # Уменьшаем остатки
    for variant_id, item in cart.items():
        decrease_stock(int(variant_id), item['qty'])
    
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
    print(f"📦 Загружено товаров: {len(get_all_variants())}")
    print("🆔 ID Бравекто таблетки: 1,2,3,4,5")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
