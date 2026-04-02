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

# ========== ID ЧАТОВ И АДМИНОВ ==========
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
ADMINS_IDS = [int(id.strip()) for id in os.environ.get("ADMINS_IDS", str(OWNER_ID)).split(",") if id.strip()]
ORDERS_CHAT_ID = int(os.environ.get("ORDERS_CHAT_ID", OWNER_ID))
REVIEWS_CHAT_LINK = os.environ.get("REVIEWS_CHAT_LINK", "https://t.me/+xxxxxxxxxxx")

# ========== СОСТОЯНИЯ ==========
class OrderForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_delivery = State()
    waiting_for_pickup_point = State()

class AdminStates(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_new_stock = State()

# ========== ТОВАРЫ ==========
PRODUCTS = {
    "antiparasitic": [
        {"id": 1, "name": "Бравекто 2-4.5 кг", "price": 1850, "desc": "Защита 12 недель\nДля собак 2-4.5 кг\nЖевательная таблетка", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 5},
        {"id": 2, "name": "Бравекто 4.5-10 кг", "price": 2150, "desc": "Защита 12 недель\nДля собак 4.5-10 кг\nЖевательная таблетка", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 3},
        {"id": 3, "name": "Бравекто 10-20 кг", "price": 2450, "desc": "Защита 12 недель\nДля собак 10-20 кг\nЖевательная таблетка", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 7},
        {"id": 4, "name": "Бравекто 20-40 кг", "price": 2850, "desc": "Защита 12 недель\nДля собак 20-40 кг\nЖевательная таблетка", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 2},
        {"id": 5, "name": "Бравекто 40-56 кг", "price": 3250, "desc": "Защита 12 недель\nДля собак 40-56 кг\nЖевательная таблетка", "photo": "https://i.imgur.com/5Q8k3lB.jpg", "stock": 4},
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

# ========== ФУНКЦИИ ==========
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
    return False

def get_all_products():
    all_products = []
    for cat in PRODUCTS.values():
        all_products.extend(cat)
    return all_products

def validate_phone(phone):
    pattern = r'^\+7\d{10}$'
    return re.match(pattern, phone) is not None

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="⭐ ОТЗЫВЫ", url=REVIEWS_CHAT_LINK)]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 ОСТАТКИ ТОВАРОВ", callback_data="admin_stock")],
        [InlineKeyboardButton(text="✏️ ИЗМЕНИТЬ ОСТАТКИ", callback_data="admin_edit_stock")],
        [InlineKeyboardButton(text="🔙 ГЛАВНОЕ МЕНЮ", callback_data="back")]
    ])

def categories_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 ОТ БЛОХ И КЛЕЩЕЙ", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 ЛЕКАРСТВА", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 ВИТАМИНЫ", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])

def product_buttons(product_id, stock, is_admin_user=False):
    """Кнопки товара - с корзиной"""
    buttons = []
    
    # Кнопка добавления в корзину (всегда есть)
    if stock > 0:
        buttons.append([InlineKeyboardButton(text="➕ В КОРЗИНУ", callback_data=f"add_{product_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="❌ НЕТ В НАЛИЧИИ", callback_data="no_stock")])
    
    # Кнопка корзины
    buttons.append([InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")])
    buttons.append([InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cart_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ ОЧИСТИТЬ", callback_data="clear")],
        [InlineKeyboardButton(text="🚚 ОФОРМИТЬ ЗАКАЗ", callback_data="checkout")]
    ])

def delivery_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ОЗОН", callback_data="delivery_ozon")],
        [InlineKeyboardButton(text="📦 WILDBERRIES", callback_data="delivery_wb")],
        [InlineKeyboardButton(text="🚚 СДЭК", callback_data="delivery_cdek")],
        [InlineKeyboardButton(text="🚛 ЯНДЕКС", callback_data="delivery_yandex")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="back")]
    ])

# ========== ПРИВЕТСТВИЕ (информация о магазине) ==========
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
        await message.answer("⛔ У вас нет доступа к админ-панели")
        return
    await message.answer("🔧 *АДМИН-ПАНЕЛЬ*\n\nУправление остатками товаров:", parse_mode="Markdown", reply_markup=admin_menu())

# ========== АДМИН-ФУНКЦИИ (только для админов) ==========
@dp.callback_query(F.data == "admin_stock")
async def admin_show_stock(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    products = get_all_products()
    text = "📊 *ТЕКУЩИЕ ОСТАТКИ:*\n\n"
    for p in products:
        text += f"🆔 *ID:{p['id']}* - {p['name']}\n   📦 Остаток: {p['stock']} шт.\n\n"
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_menu())
    await call.answer()

@dp.callback_query(F.data == "admin_edit_stock")
async def admin_edit_stock_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа")
        return
    products = get_all_products()
    text = "✏️ *ВВЕДИТЕ ID ТОВАРА:*\n\n"
    for p in products:
        text += f"🆔 ID: {p['id']} - {p['name']} (остаток: {p['stock']})\n"
    await call.message.edit_text(text, parse_mode="Markdown")
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
            await message.answer(f"📦 *{product['name']}*\n📊 Текущий остаток: {product['stock']} шт.\n\n✏️ *ВВЕДИТЕ НОВЫЙ ОСТАТОК:*", parse_mode="Markdown")
            await state.set_state(AdminStates.waiting_for_new_stock)
        else:
            await message.answer("❌ Товар не найден. Попробуйте еще раз:")
    except ValueError:
        await message.answer("❌ Введите число (ID товара)")

@dp.message(AdminStates.waiting_for_new_stock)
async def admin_set_new_stock(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        new_stock = int(message.text)
        data = await state.get_data()
        product_id = data['product_id']
        update_product_stock(product_id, new_stock)
        await message.answer(f"✅ *ОСТАТКИ ОБНОВЛЕНЫ!*\n🆔 ID: {product_id}\n📦 Новый остаток: {new_stock} шт.", parse_mode="Markdown", reply_markup=admin_menu())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число")

# ========== КАТАЛОГ ==========
@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    await call.message.edit_text("📁 *ВЫБЕРИТЕ КАТЕГОРИЮ:*", parse_mode="Markdown", reply_markup=categories_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_products(call: CallbackQuery):
    category = call.data.split("_")[1]
    products = PRODUCTS.get(category, [])
    if not products:
        await call.message.edit_text("😕 Товаров нет")
        return
    await call.message.edit_text("📦 *ВОТ ЧТО МЫ НАШЛИ:*", parse_mode="Markdown")
    
    is_admin_user = is_admin(call.from_user.id)
    
    for product in products:
        stock = product['stock']
        
        # Формируем текст: для админов показываем остатки, для клиентов - нет
        text = f"*{product['name']}*\n\n{product['desc']}\n\n💰 *{product['price']} руб.*"
        
        # Только админы видят остатки
        if is_admin_user:
            if stock > 0:
                text += f"\n📦 *В наличии: {stock} шт.*"
            else:
                text += f"\n❌ *НЕТ В НАЛИЧИИ*"
        
        try:
            await call.message.answer_photo(
                photo=product['photo'], 
                caption=text, 
                parse_mode="Markdown", 
                reply_markup=product_buttons(product['id'], stock, is_admin_user)
            )
        except:
            await call.message.answer(
                text, 
                parse_mode="Markdown", 
                reply_markup=product_buttons(product['id'], stock, is_admin_user)
            )
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
    current_stock = product['stock']
    current_in_cart = carts.get(user_id, {}).get(product_id, {}).get('qty', 0)
    
    if current_in_cart >= current_stock:
        await call.answer(f"❌ НЕЛЬЗЯ ДОБАВИТЬ БОЛЬШЕ!\n📦 В наличии: {current_stock} шт.\n🛒 Уже в корзине: {current_in_cart} шт.", show_alert=True)
        return
    
    if user_id not in carts:
        carts[user_id] = {}
    if product_id in carts[user_id]:
        carts[user_id][product_id]['qty'] += 1
    else:
        carts[user_id][product_id] = {'name': product['name'], 'price': product['price'], 'qty': 1}
    
    new_in_cart = current_in_cart + 1
    remaining = current_stock - new_in_cart
    
    await call.answer(f"✅ {product['name']}\nДОБАВЛЕН!\n📦 В корзине: {new_in_cart} шт.\n📦 Осталось: {remaining} шт.", show_alert=True)

@dp.callback_query(F.data == "no_stock")
async def no_stock_handler(call: CallbackQuery):
    await call.answer("❌ Товар временно отсутствует!", show_alert=True)

# ========== КОРЗИНА ==========
@dp.callback_query(F.data == "cart")
async def view_cart(call: CallbackQuery):
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    if not cart:
        await call.message.edit_text("🛒 *КОРЗИНА ПУСТА*\n\nДобавьте товары из каталога", parse_mode="Markdown", reply_markup=main_menu())
        return
    total = 0
    total_items = 0
    text = "🛒 *ВАША КОРЗИНА*\n\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"📦 *{item['name']}*\n   {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
        total_items += item['qty']
    text += "━━━━━━━━━━━━━━━━━━━━\n📦 *ИТОГО:* {total_items} шт.\n💰 *СУММА:* {total} руб."
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=cart_buttons())
    await call.answer()

@dp.callback_query(F.data == "clear")
async def clear_cart(call: CallbackQuery):
    carts[call.from_user.id] = {}
    await call.message.edit_text("🗑️ *КОРЗИНА ОЧИЩЕНА*", parse_mode="Markdown", reply_markup=main_menu())
    await call.answer()

# ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========
@dp.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    if not cart:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    await call.message.edit_text("📝 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\nШаг 1 из 4\n\n✏️ *ВВЕДИТЕ ВАШЕ ИМЯ:*\n\nНапример: Иван", parse_mode="Markdown")
    await state.set_state(OrderForm.waiting_for_name)
    await call.answer()

@dp.message(OrderForm.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Введите корректное имя (минимум 2 буквы):")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("📝 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\nШаг 2 из 4\n\n📱 *ВВЕДИТЕ НОМЕР ТЕЛЕФОНА:*\n\nФормат: +7XXXXXXXXXX\nПример: +79001234567", parse_mode="Markdown")
    await state.set_state(OrderForm.waiting_for_phone)

@dp.message(OrderForm.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not validate_phone(phone):
        await message.answer("❌ *НЕВЕРНЫЙ ФОРМАТ!*\n\nВведите номер в формате +7XXXXXXXXXX", parse_mode="Markdown")
        return
    await state.update_data(phone=phone)
    await message.answer("📝 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\nШаг 3 из 4\n\n🚚 *ВЫБЕРИТЕ СЛУЖБУ ДОСТАВКИ:*", parse_mode="Markdown", reply_markup=delivery_menu())
    await state.set_state(OrderForm.waiting_for_delivery)

@dp.callback_query(OrderForm.waiting_for_delivery, F.data.startswith("delivery_"))
async def select_delivery(call: CallbackQuery, state: FSMContext):
    service = call.data.split("_")[1]
    await state.update_data(delivery=service)
    await call.message.edit_text("📝 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\nШаг 4 из 4 (последний)\n\n🏠 *УКАЖИТЕ АДРЕС ПУНКТА ВЫДАЧИ,*\nгде вам удобно забрать заказ:\n\nНапример: г. Москва, м. Первомайская, ул. Первомайская, д. 1", parse_mode="Markdown")
    await state.set_state(OrderForm.waiting_for_pickup_point)
    await call.answer()

@dp.message(OrderForm.waiting_for_pickup_point)
async def get_pickup_point(message: Message, state: FSMContext):
    pickup_point = message.text.strip()
    if len(pickup_point) < 10:
        await message.answer("❌ Введите полный адрес пункта выдачи (минимум 10 символов):")
        return
    await state.update_data(pickup_point=pickup_point)
    data = await state.get_data()
    name = data['name']
    phone = data['phone']
    delivery = data['delivery']
    pickup_point = data['pickup_point']
    user_id = message.from_user.id
    cart = carts.get(user_id, {})
    if not cart:
        await message.answer("❌ Корзина пуста!", reply_markup=main_menu())
        await state.clear()
        return
    
    # Проверяем остатки
    can_checkout = True
    for product_id, item in cart.items():
        current_stock = get_product_stock(int(product_id))
        if item['qty'] > current_stock:
            can_checkout = False
            await message.answer(f"❌ Невозможно оформить заказ!\n{item['name']} - в наличии {current_stock} шт.", parse_mode="Markdown")
            break
    
    if not can_checkout:
        await state.clear()
        return
    
    # Уменьшаем остатки
    for product_id, item in cart.items():
        decrease_stock(int(product_id), item['qty'])
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    total_items = sum(item['qty'] for item in cart.values())
    
    # Формируем заказ
    order_text = f"✅ *НОВЫЙ ЗАКАЗ!*\n\n"
    order_text += f"👤 Имя: {name}\n"
    order_text += f"📱 Телефон: {phone}\n"
    order_text += f"🚚 Служба: {delivery.upper()}\n"
    order_text += f"🏠 Пункт выдачи: {pickup_point}\n"
    order_text += f"🆔 ID покупателя: {user_id}\n\n"
    order_text += f"📦 *ТОВАРЫ:*\n"
    
    for item in cart.values():
        order_text += f"• {item['name']} x{item['qty']} = {item['price'] * item['qty']} руб.\n"
    
    order_text += f"\n💰 *ИТОГО:* {total} руб.\n"
    order_text += f"📦 *ВСЕГО ТОВАРОВ:* {total_items} шт."
    
    # Отправляем заказ в отдельный чат
    try:
        await bot.send_message(chat_id=ORDERS_CHAT_ID, text=order_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки в чат: {e}")
    
    # Очищаем корзину
    carts[user_id] = {}
    await state.clear()
    
    await message.answer(
        f"✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
        f"👤 {name}\n"
        f"📱 {phone}\n"
        f"🚚 {delivery.upper()}\n"
        f"🏠 {pickup_point}\n"
        f"💰 {total} руб.\n\n"
        f"Скоро свяжется менеджер.\n\n"
        f"🐕 Спасибо за покупку!\n\n"
        f"⭐ *Оставьте отзыв в разделе 'ОТЗЫВЫ'*",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
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
    
    await call.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=main_menu())
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    print(f"👥 Админы: {ADMINS_IDS}")
    print(f"📦 Заказы отправляются в чат: {ORDERS_CHAT_ID}")
    print("🔧 Админ-панель: /admin")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
