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
    waiting_for_new_stock = State()

# ========== ТОВАРЫ ==========
PRODUCTS = {
    "antiparasitic": [
        {"id": 1, "name": "Бравекто 2-4.5 кг", "price": 1850, "desc": "Защита 12 недель\nДля собак 2-4.5 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 5},
        {"id": 2, "name": "Бравекто 4.5-10 кг", "price": 2150, "desc": "Защита 12 недель\nДля собак 4.5-10 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 3},
        {"id": 3, "name": "Бравекто 10-20 кг", "price": 2450, "desc": "Защита 12 недель\nДля собак 10-20 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 7},
        {"id": 4, "name": "Бравекто 20-40 кг", "price": 2850, "desc": "Защита 12 недель\nДля собак 20-40 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 2},
        {"id": 5, "name": "Бравекто 40-56 кг", "price": 3250, "desc": "Защита 12 недель\nДля собак 40-56 кг", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 4},
        {"id": 6, "name": "Нексгард 4-10 кг", "price": 1950, "desc": "Защита 1 месяц\nДля собак 4-10 кг\n3 таблетки", "photo": "https://i.imgur.com/LpQxE6k.jpg", "stock": 8},
        {"id": 7, "name": "Симпарика 5-10 кг", "price": 1850, "desc": "Защита 1 месяц\nДля собак 5-10 кг\n3 таблетки", "photo": "https://i.imgur.com/WK9qP5c.jpg", "stock": 6},
    ],
    "medicine": [
        {"id": 8, "name": "Стоп-зуд", "price": 890, "desc": "Антигистаминный\nОт аллергического зуда\n20 таблеток", "photo": "https://i.imgur.com/8Qk3lB.jpg", "stock": 10},
        {"id": 9, "name": "Энтеросгель", "price": 450, "desc": "Энтеросорбент\nПри отравлениях\n225 г", "photo": "https://i.imgur.com/9Qk3lB.jpg", "stock": 15},
    ],
    "vitamins": [
        {"id": 10, "name": "Глюкозамин", "price": 1250, "desc": "Для суставов\nДля крупных пород\n90 таблеток", "photo": "https://i.imgur.com/glucosamine.jpg", "stock": 12},
        {"id": 11, "name": "Омега-3", "price": 980, "desc": "Для шерсти\nУлучшает состояние\n60 капсул", "photo": "https://i.imgur.com/omega3.jpg", "stock": 20},
    ],
}

carts = {}

def is_admin(user_id):
    return user_id in ADMINS_IDS

def get_product_stock(product_id):
    for cat in PRODUCTS.values():
        for p in cat:
            if p['id'] == product_id:
                return p['stock']
    return 0

def update_product_stock(product_id, new_stock):
    for cat in PRODUCTS.values():
        for p in cat:
            if p['id'] == product_id:
                p['stock'] = new_stock
                return True
    return False

def decrease_stock(product_id, quantity):
    for cat in PRODUCTS.values():
        for p in cat:
            if p['id'] == product_id:
                if p['stock'] >= quantity:
                    p['stock'] -= quantity
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
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="show_cart")],
        [InlineKeyboardButton(text="⭐ ОТЗЫВЫ", url=REVIEWS_CHAT_LINK)]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 ОСТАТКИ", callback_data="admin_stock")],
        [InlineKeyboardButton(text="✏️ ИЗМЕНИТЬ", callback_data="admin_edit_stock")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="main_back")]
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

🚘 В Москве, по согласованию, возможен самовывоз (м. Первомайская, оплата наличными). 

💡 Отправления Яндекс, Озон или СДЭК.

👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇"""
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer("🔧 АДМИН-ПАНЕЛЬ", reply_markup=admin_menu())

# ========== АДМИН ==========
@dp.callback_query(F.data == "admin_stock")
async def admin_show_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    products = get_all_products()
    text = "📊 ОСТАТКИ:\n\n"
    for p in products:
        text += f"ID {p['id']} - {p['name']}\n   📦 {p['stock']} шт.\n\n"
    await call.message.answer(text, reply_markup=admin_menu())
    await call.message.delete()
    await call.answer()

@dp.callback_query(F.data == "admin_edit_stock")
async def admin_edit_stock_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    products = get_all_products()
    text = "✏️ ВВЕДИТЕ ID ТОВАРА:\n\n"
    for p in products:
        text += f"ID {p['id']} - {p['name']} (остаток: {p['stock']})\n"
    await call.message.answer(text)
    await call.message.delete()
    await state.set_state(AdminStates.waiting_for_product_id)
    await call.answer()

@dp.message(AdminStates.waiting_for_product_id)
async def admin_get_product_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        product_id = int(message.text)
        product = None
        for p in get_all_products():
            if p['id'] == product_id:
                product = p
                break
        if product:
            await state.update_data(product_id=product_id)
            await message.answer(f"📦 {product['name']}\nТекущий остаток: {product['stock']} шт.\n\nВВЕДИТЕ НОВЫЙ ОСТАТОК:")
            await state.set_state(AdminStates.waiting_for_new_stock)
        else:
            await message.answer("❌ Товар не найден")
    except ValueError:
        await message.answer("❌ Введите число")

@dp.message(AdminStates.waiting_for_new_stock)
async def admin_set_new_stock(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        new_stock = int(message.text)
        data = await state.get_data()
        product_id = data['product_id']
        update_product_stock(product_id, new_stock)
        await message.answer(f"✅ ОБНОВЛЕНО!\nID {product_id}\nНовый остаток: {new_stock} шт.", reply_markup=admin_menu())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число")

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
    
    for product in products:
        stock = product['stock']
        text = f"{product['name']}\n\n{product['desc']}\n\n💰 {product['price']} руб."
        try:
            await call.message.answer_photo(photo=product['photo'], caption=text, reply_markup=product_buttons(product['id'], stock))
        except:
            await call.message.answer(text, reply_markup=product_buttons(product['id'], stock))
    await call.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    product = None
    for cat in PRODUCTS.values():
        for p in cat:
            if p['id'] == product_id:
                product = p
                break
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
    # Преобразуем samovyvoz в читаемый вид
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
    
    for product_id, item in cart.items():
        current_stock = get_product_stock(int(product_id))
        if item['qty'] > current_stock:
            await message.answer(f"❌ Невозможно оформить заказ!\n{item['name']} - в наличии {current_stock} шт.")
            await state.clear()
            return
    
    for product_id, item in cart.items():
        decrease_stock(int(product_id), item['qty'])
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    total_items = sum(item['qty'] for item in cart.values())
    
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
    
    try:
        await bot.send_message(chat_id=ORDERS_CHAT_ID, text=order_text)
    except Exception as e:
        print(f"Ошибка: {e}")
    
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

🚘 В Москве, по согласованию, возможен самовывоз (м. Первомайская, оплата наличными). 

💡 Отправления Яндекс, Озон или СДЭК.

👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇"""
    
    await call.message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())
    await call.message.delete()
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
