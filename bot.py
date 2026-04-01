import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
import urllib.request

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ТОВАРЫ С КАРТИНКАМИ ==========
# Используем прямые ссылки на фото препаратов
PRODUCTS = {
    "antiparasitic": [
        {
            "id": 1, 
            "name": "🟢 Бравекто 2-4.5 кг", 
            "price": 1850, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 2-4.5 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 2, 
            "name": "🟢 Бравекто 4.5-10 кг", 
            "price": 2150, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 4.5-10 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 3, 
            "name": "🟢 Бравекто 10-20 кг", 
            "price": 2450, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 10-20 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 4, 
            "name": "🟢 Бравекто 20-40 кг", 
            "price": 2850, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 20-40 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 5, 
            "name": "🟢 Бравекто 40-56 кг", 
            "price": 3250, 
            "desc": "✅ Защита 12 недель\n🐕 Для собак 40-56 кг\n💊 Жевательная таблетка",
            "photo": "https://i.imgur.com/5Q8k3lB.jpg"
        },
        {
            "id": 6, 
            "name": "🔵 Нексгард 4-10 кг", 
            "price": 1950, 
            "desc": "✅ Защита 1 месяц\n🐕 Для собак 4-10 кг\n📦 3 таблетки",
            "photo": "https://i.imgur.com/LpQxE6k.jpg"
        },
        {
            "id": 7, 
            "name": "🟠 Симпарика 5-10 кг", 
            "price": 1850, 
            "desc": "✅ Защита 1 месяц\n🐕 Для собак 5-10 кг\n📦 3 таблетки",
            "photo": "https://i.imgur.com/WK9qP5c.jpg"
        },
    ],
    "medicine": [
        {
            "id": 8, 
            "name": "💊 Стоп-зуд", 
            "price": 890, 
            "desc": "✅ Антигистаминный\n🐕 От аллергического зуда\n📦 20 таблеток",
            "photo": "https://i.imgur.com/stopitch.jpg"
        },
        {
            "id": 9, 
            "name": "💊 Энтеросгель", 
            "price": 450, 
            "desc": "✅ Энтеросорбент\n🐕 При отравлениях\n📦 225 г",
            "photo": "https://i.imgur.com/enterosgel.jpg"
        },
    ],
    "vitamins": [
        {
            "id": 10, 
            "name": "🦴 Глюкозамин", 
            "price": 1250, 
            "desc": "✅ Для суставов\n🐕 Для крупных пород\n📦 90 таблеток",
            "photo": "https://i.imgur.com/glucosamine.jpg"
        },
        {
            "id": 11, 
            "name": "🐟 Омега-3", 
            "price": 980, 
            "desc": "✅ Для шерсти\n🐕 Улучшает состояние\n📦 60 капсул",
            "photo": "https://i.imgur.com/omega3.jpg"
        },
    ]
}

carts = {}

# ========== КЛАВИАТУРЫ ==========

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ КАТАЛОГ ТОВАРОВ", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="ℹ️ О МАГАЗИНЕ", callback_data="about")]
    ])

def categories_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 ОТ БЛОХ И КЛЕЩЕЙ", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 ЛЕКАРСТВА", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 ВИТАМИНЫ", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="back")]
    ])

def product_buttons(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ ДОБАВИТЬ В КОРЗИНУ", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🛒 КОРЗИНА", callback_data="cart")],
        [InlineKeyboardButton(text="📁 К КАТАЛОГУ", callback_data="catalog")]
    ])

def cart_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ ОЧИСТИТЬ КОРЗИНУ", callback_data="clear")],
        [InlineKeyboardButton(text="✅ ОФОРМИТЬ ЗАКАЗ", callback_data="checkout")],
        [InlineKeyboardButton(text="🛍️ ПРОДОЛЖИТЬ ПОКУПКИ", callback_data="catalog")]
    ])

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="back")]
    ])

# ========== КОМАНДЫ ==========

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✨ *Оригинальные препараты*\n"
        "🚚 *Доставка по всей России*\n"
        "💊 *Бравекто, Нексгард, Симпарика*\n\n"
        "👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

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
    
    await call.message.edit_text(
        "📦 *ВОТ ЧТО МЫ НАШЛИ:*",
        parse_mode="Markdown"
    )
    
    for product in products:
        text = f"*{product['name']}*\n\n"
        text += f"{product['desc']}\n\n"
        text += f"💰 *Цена: {product['price']} руб.*"
        
        # Отправляем с картинкой
        try:
            await call.message.answer_photo(
                photo=product['photo'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=product_buttons(product['id'])
            )
        except:
            # Если картинка не загружается, отправляем без картинки
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
    text += f"📦 *ИТОГО ТОВАРОВ:* {total_items} шт.\n"
    text += f"💰 *СУММА К ОПЛАТЕ:* {total} руб."
    
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
        "🗑️ *КОРЗИНА ОЧИЩЕНА*\n\n"
        "Можете продолжить покупки в каталоге",
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
        "✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
        f"📦 *Товаров:* {total_items} шт.\n"
        f"💰 *Сумма:* {total} руб.\n\n"
        "📞 *Что дальше?*\n"
        "Скоро с вами свяжется менеджер\n"
        "для подтверждения заказа.\n\n"
        "🐕 *Спасибо за покупку!*",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = """🐕 *VetProfil - ветеринарная аптека*

━━━━━━━━━━━━━━━━━━━━
📦 *МЫ ПРЕДЛАГАЕМ:*
• Бравекто (все размеры) с фото
• Нексгард с фото
• Симпарика с фото
• Лекарства и витамины с фото

🚚 *ДОСТАВКА:*
• Озон
• Wildberries  
• СДЭК
• Яндекс Доставка

💊 *Все препараты сертифицированы*
🖼️ *Все товары с фото*
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
        "✨ *Оригинальные препараты*\n"
        "🚚 *Доставка по всей России*\n"
        "💊 *Бравекто, Нексгард, Симпарика*\n\n"
        "👇 *ВЫБЕРИТЕ ДЕЙСТВИЕ* 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    print("🖼️ ВСЕ ТОВАРЫ С КАРТИНКАМИ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
