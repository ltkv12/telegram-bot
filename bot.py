import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== СОСТОЯНИЯ ДЛЯ АДРЕСА ==========
class AddressForm(StatesGroup):
    waiting_for_address = State()

# ========== ТОВАРЫ С КАРТИНКАМИ ==========
PRODUCTS = {
    "antiparasitic": [
        {
            "id": 1, 
            "name": "Бравекто 2-4.5 кг", 
            "price": 1850, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 2-4.5 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 2, 
            "name": "Бравекто 4.5-10 кг", 
            "price": 2150, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 4.5-10 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 3, 
            "name": "Бравекто 10-20 кг", 
            "price": 2450, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 10-20 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 4, 
            "name": "Бравекто 20-40 кг", 
            "price": 2850, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 20-40 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 5, 
            "name": "Бравекто 40-56 кг", 
            "price": 3250, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 40-56 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 6, 
            "name": "Нексгард 4-10 кг", 
            "price": 1950, 
            "desc": "✅ Защита 1 месяц\n🐕 Для собак 4-10 кг\n📦 3 таблетки",
            "photo": "https://i.imgur.com/LpQxE6k.jpg"
        },
        {
            "id": 7, 
            "name": "Симпарика 5-10 кг", 
            "price": 1850, 
            "desc": "✅ Защита 1 месяц\n🐕 Для собак 5-10 кг\n📦 3 таблетки",
            "photo": "https://i.imgur.com/WK9qP5c.jpg"
        },
    ],
    "medicine": [
        {
            "id": 8, 
            "name": "Стоп-зуд", 
            "price": 890, 
            "desc": "✅ Антигистаминный\n🐕 От аллергического зуда\n📦 20 таблеток",
            "photo": "https://i.imgur.com/8Qk3lB.jpg"
        },
        {
            "id": 9, 
            "name": "Энтеросгель", 
            "price": 450, 
            "desc": "✅ Энтеросорбент\n🐕 При отравлениях\n📦 225 г",
            "photo": "https://i.imgur.com/9Qk3lB.jpg"
        },
    ],
    "vitamins": [
        {
            "id": 10, 
            "name": "Глюкозамин", 
            "price": 1250, 
            "desc": "✅ Для суставов\n🐕 Для крупных пород\n📦 90 таблеток",
            "photo": "https://i.imgur.com/glucosamine.jpg"
        },
        {
            "id": 11, 
            "name": "Омега-3", 
            "price": 980, 
            "desc": "✅ Для шерсти\n🐕 Улучшает состояние\n📦 60 капсул",
            "photo": "https://i.imgur.com/omega3.jpg"
        },
    ]
}

carts = {}
delivery_services = {}
last_message_ids = {}  # Храним ID последнего сообщения для редактирования

# ========== КЛАВИАТУРЫ ==========

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="ℹ️ О НАС", callback_data="about")]
    ])

def categories_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 ОТ БЛОХ И КЛЕЩЕЙ", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 ЛЕКАРСТВА", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 ВИТАМИНЫ", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])

def product_buttons(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ В КОРЗИНУ", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")]
    ])

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

# ========== КОМАНДЫ ==========

@dp.message(Command("start"))
async def start(message: Message):
    msg = await message.answer(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✨ Оригинальные препараты\n"
        "🚚 Доставка по всей России\n"
        "💊 Бравекто, Нексгард, Симпарика\n\n"
        "👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    last_message_ids[message.from_user.id] = msg.message_id

@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    await call.message.edit_text(
        "📁 *ВЫБЕРИТЕ КАТЕГОРИЮ:*",
        parse_mode="Markdown",
        reply_markup=categories_menu()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_products(call: CallbackQuery):
    category = call.data.split("_")[1]
    products = PRODUCTS.get(category, [])
    
    if not products:
        await call.message.edit_text("😕 Товаров в этой категории пока нет")
        return
    
    # Отправляем сообщение с текстом
    await call.message.edit_text(
        "📦 *ВОТ ЧТО МЫ НАШЛИ:*",
        parse_mode="Markdown"
    )
    
    # Отправляем каждый товар отдельно
    for product in products:
        text = f"*{product['name']}*\n\n"
        text += f"{product['desc']}\n\n"
        text += f"💰 *Цена: {product['price']} руб.*"
        
        try:
            await call.message.answer_photo(
                photo=product['photo'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=product_buttons(product['id'])
            )
        except:
            await call.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=product_buttons(product['id'])
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
    
    if user_id not in carts:
        carts[user_id] = {}
    
    if product_id in carts[user_id]:
        carts[user_id][product_id]['qty'] += 1
    else:
        carts[user_id][product_id] = {
            'name': product['name'],
            'price': product['price'],
            'qty': 1
        }
    
    total_items = sum(item['qty'] for item in carts[user_id].values())
    
    await call.answer(
        f"✅ {product['name']}\n"
        f"ДОБАВЛЕН В КОРЗИНУ!\n\n"
        f"📦 В корзине: {total_items} товар(ов)",
        show_alert=True
    )

@dp.callback_query(F.data == "cart")
async def view_cart(call: CallbackQuery):
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    
    if not cart:
        await call.message.edit_text(
            "🛒 *КОРЗИНА ПУСТА*\n\n"
            "Добавьте товары из каталога",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return
    
    total = 0
    total_items = 0
    text = "🛒 *ВАША КОРЗИНА*\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"📦 *{item['name']}*\n"
        text += f"   {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
        total_items += item['qty']
    
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📦 *ИТОГО:* {total_items} шт.\n"
    text += f"💰 *СУММА:* {total} руб."
    
    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=cart_buttons()
    )
    await call.answer()

@dp.callback_query(F.data == "clear")
async def clear_cart(call: CallbackQuery):
    carts[call.from_user.id] = {}
    await call.message.edit_text(
        "🗑️ *КОРЗИНА ОЧИЩЕНА*",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery):
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    
    if not cart:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    await call.message.edit_text(
        "🚚 *ВЫБЕРИТЕ СЛУЖБУ ДОСТАВКИ:*",
        parse_mode="Markdown",
        reply_markup=delivery_menu()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("delivery_"))
async def select_delivery(call: CallbackQuery, state: FSMContext):
    service = call.data.split("_")[1]
    user_id = call.from_user.id
    
    delivery_services[user_id] = service
    
    await call.message.edit_text(
        f"📦 *ВЫБРАНА СЛУЖБА:* {service.upper()}\n\n"
        "🏠 *ВВЕДИТЕ АДРЕС ДОСТАВКИ:*\n\n"
        "Например: г. Москва, ул. Тверская, д. 1",
        parse_mode="Markdown"
    )
    await state.set_state(AddressForm.waiting_for_address)
    await call.answer()

@dp.message(AddressForm.waiting_for_address)
async def get_address(message: Message, state: FSMContext):
    user_id = message.from_user.id
    address = message.text
    service = delivery_services.get(user_id, "не выбрана")
    cart = carts.get(user_id, {})
    
    if not cart:
        await message.answer("Корзина пуста!", reply_markup=main_menu())
        await state.clear()
        return
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    total_items = sum(item['qty'] for item in cart.values())
    
    # Формируем заказ
    order_text = f"✅ *НОВЫЙ ЗАКАЗ!*\n\n"
    order_text += f"👤 Клиент: {message.from_user.full_name}\n"
    order_text += f"🆔 ID: {user_id}\n"
    order_text += f"🚚 Служба: {service.upper()}\n"
    order_text += f"🏠 Адрес: {address}\n\n"
    order_text += f"📦 Товары:\n"
    
    for item in cart.values():
        order_text += f"• {item['name']} x{item['qty']} = {item['price'] * item['qty']} руб.\n"
    
    order_text += f"\n💰 Итого: {total} руб."
    
    # Отправляем заказ продавцу
    seller_id = os.environ.get("SELLER_CHAT_ID", user_id)
    try:
        await bot.send_message(chat_id=seller_id, text=order_text, parse_mode="Markdown")
    except:
        pass
    
    # Очищаем корзину
    carts[user_id] = {}
    await state.clear()
    
    await message.answer(
        f"✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
        f"📦 Служба: {service.upper()}\n"
        f"🏠 Адрес: {address}\n"
        f"💰 Сумма: {total} руб.\n\n"
        f"Скоро с вами свяжется менеджер для подтверждения.\n\n"
        f"🐕 Спасибо за покупку!",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = """🐕 *VetProfil - ветеринарная аптека*

━━━━━━━━━━━━━━━━━━━━
📦 *МЫ ПРЕДЛАГАЕМ:*
• Бравекто (все размеры)
• Нексгард
• Симпарика
• Лекарства и витамины

🚚 *ДОСТАВКА:*
• Озон
• Wildberries  
• СДЭК
• Яндекс Доставка

💊 *Все препараты сертифицированы*
━━━━━━━━━━━━━━━━━━━━"""
    
    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_to_main()
    )
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.message.edit_text(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✨ Оригинальные препараты\n"
        "🚚 Доставка по всей России\n"
        "💊 Бравекто, Нексгард, Симпарика\n\n"
        "👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    print("✅ Исправлена ошибка с редактированием")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
