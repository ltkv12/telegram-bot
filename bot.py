import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Товары
PRODUCTS = {
    "antiparasitic": [
        {"id": 1, "name": "Бравекто 2-4.5 кг", "price": 1850, "desc": "Защита 12 недель\nДля собак 2-4.5 кг"},
        {"id": 2, "name": "Бравекто 4.5-10 кг", "price": 2150, "desc": "Защита 12 недель\nДля собак 4.5-10 кг"},
        {"id": 3, "name": "Бравекто 10-20 кг", "price": 2450, "desc": "Защита 12 недель\nДля собак 10-20 кг"},
        {"id": 4, "name": "Нексгард 4-10 кг", "price": 1950, "desc": "Защита 1 месяц\n3 таблетки"},
    ],
    "medicine": [
        {"id": 5, "name": "Стоп-зуд", "price": 890, "desc": "От аллергии\n20 таблеток"},
    ],
    "vitamins": [
        {"id": 6, "name": "Глюкозамин", "price": 1250, "desc": "Для суставов\n90 таблеток"},
        {"id": 7, "name": "Омега-3", "price": 980, "desc": "Для шерсти\n60 капсул"},
    ]
}

carts = {}

# ========== ВСЕ МЕНЮ С КОРЗИНОЙ ==========

def main_menu():
    """Главное меню - КОРЗИНА ВСЕГДА ВИДНА"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 КАТАЛОГ", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА 🛒", callback_data="cart")],
        [InlineKeyboardButton(text="ℹ️ О НАС", callback_data="about")]
    ])

def categories_menu():
    """Меню категорий - С КОРЗИНОЙ"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 ОТ БЛОХ И КЛЕЩЕЙ", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 ЛЕКАРСТВА", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 ВИТАМИНЫ", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА 🛒", callback_data="cart")],
        [InlineKeyboardButton(text="◀️ ГЛАВНОЕ МЕНЮ", callback_data="back")]
    ])

def product_buttons(product_id):
    """Кнопки товара - С КОРЗИНОЙ"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ В КОРЗИНУ", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА 🛒", callback_data="cart")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="catalog")]
    ])

def cart_buttons():
    """Кнопки корзины"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 ОЧИСТИТЬ", callback_data="clear")],
        [InlineKeyboardButton(text="✅ ОФОРМИТЬ ЗАКАЗ", callback_data="checkout")],
        [InlineKeyboardButton(text="🛍 ПРОДОЛЖИТЬ ПОКУПКИ", callback_data="catalog")]
    ])

def back_menu():
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ ГЛАВНОЕ МЕНЮ", callback_data="back")]
    ])

# ========== КОМАНДЫ ==========

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✅ Оригинальные препараты\n"
        "🚚 Доставка по всей России\n"
        "💊 Бравекто, Нексгард, Симпарика\n\n"
        "🛒 *КОРЗИНА ВСЕГДА ПОД РУКОЙ!*\n\n"
        "👇 Нажмите кнопку ниже 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    await call.message.edit_text(
        "📁 *ВЫБЕРИТЕ КАТЕГОРИЮ:*\n\n"
        "🛒 Кнопка КОРЗИНА всегда внизу",
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
    
    await call.message.edit_text(
        f"📦 *ТОВАРЫ В КАТЕГОРИИ:*\n\n"
        f"🛒 Кнопка КОРЗИНА есть у каждого товара",
        parse_mode="Markdown"
    )
    
    for product in products:
        text = f"*{product['name']}*\n\n"
        text += f"{product['desc']}\n\n"
        text += f"💰 *{product['price']} руб.*"
        
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
        f"✅ {product['name']} ДОБАВЛЕН!\n"
        f"📦 В КОРЗИНЕ: {total_items} ТОВАР(ОВ)",
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
    text = "🛒 *ВАША КОРЗИНА:*\n\n"
    
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"• {item['name']}\n"
        text += f"  {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
        total_items += item['qty']
    
    text += f"📦 *ВСЕГО ТОВАРОВ:* {total_items} шт.\n"
    text += f"💰 *ИТОГО:* {total} руб."
    
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
        "🗑 *КОРЗИНА ОЧИЩЕНА!*\n\n"
        "Добавьте новые товары в каталоге",
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
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    total_items = sum(item['qty'] for item in cart.values())
    
    carts[user_id] = {}
    
    await call.message.edit_text(
        f"✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
        f"📦 Товаров: {total_items} шт.\n"
        f"💰 Сумма: {total} руб.\n\n"
        f"Скоро с вами свяжется менеджер.\n\n"
        f"Спасибо за покупку! 🐕",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = """🐕 *VetProfil - ветеринарная аптека*

📦 *Мы предлагаем:*
• Бравекто (все размеры)
• Нексгард
• Симпарика
• Лекарства и витамины

🚚 *Доставка:* Озон, Wildberries, СДЭК, Яндекс

💊 *Все препараты сертифицированы*

🛒 *КОРЗИНА ВСЕГДА ВНИЗУ!*"""
    
    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.message.edit_text(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✅ Оригинальные препараты\n"
        "🚚 Доставка по всей России\n\n"
        "🛒 *КОРЗИНА ВСЕГДА ПОД РУКОЙ!*",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    print("🛒 КОРЗИНА ТЕПЕРЬ ВЕЗДЕ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
