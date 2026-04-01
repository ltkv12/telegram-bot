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
        {"id": 4, "name": "Бравекто 20-40 кг", "price": 2850, "desc": "Защита 12 недель\nДля собак 20-40 кг"},
        {"id": 5, "name": "Бравекто 40-56 кг", "price": 3250, "desc": "Защита 12 недель\nДля собак 40-56 кг"},
        {"id": 6, "name": "Нексгард 4-10 кг", "price": 1950, "desc": "Защита 1 месяц\n3 таблетки"},
    ],
    "medicine": [
        {"id": 7, "name": "Стоп-зуд", "price": 890, "desc": "От аллергии\n20 таблеток"},
        {"id": 8, "name": "Энтеросгель", "price": 450, "desc": "При отравлениях\n225 г"},
    ],
    "vitamins": [
        {"id": 9, "name": "Глюкозамин", "price": 1250, "desc": "Для суставов\n90 таблеток"},
        {"id": 10, "name": "Омега-3", "price": 980, "desc": "Для шерсти\n60 капсул"},
    ]
}

carts = {}

# ========== ГЛАВНОЕ МЕНЮ (КОРЗИНА ВСЕГДА ВИДНА) ==========
def main_menu():
    """Главное меню с корзиной"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Корзина 🛒", callback_data="cart")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")]
    ])

def categories_menu():
    """Меню категорий"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 От блох и клещей", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 Лекарства", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 Витамины", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🛒 Корзина 🛒", callback_data="cart")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back")]
    ])

def product_buttons(product_id):
    """Кнопки товара (корзина всегда видна)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🛒 Корзина 🛒", callback_data="cart")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
    ])

def cart_buttons():
    """Кнопки корзины"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear")],
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🛍 Продолжить покупки", callback_data="catalog")]
    ])

def about_kb():
    """Кнопка возврата"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back")]
    ])

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def start(message: Message):
    """Приветствие"""
    await message.answer(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✅ Оригинальные препараты\n"
        "🚚 Доставка по всей России\n"
        "💊 Бравекто, Нексгард, Симпарика\n\n"
        "🛒 *Корзина всегда под рукой* - кнопка внизу",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    """Показывает категории"""
    await call.message.edit_text(
        "📁 *Выберите категорию:*\n\n"
        "🛒 Корзина доступна внизу",
        parse_mode="Markdown",
        reply_markup=categories_menu()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_products(call: CallbackQuery):
    """Показывает товары в категории"""
    category = call.data.split("_")[1]
    products = PRODUCTS.get(category, [])
    
    if not products:
        await call.message.edit_text("😕 Товаров в этой категории пока нет")
        return
    
    # Сначала показываем категорию
    await call.message.edit_text(
        f"📦 *Товары в категории:*\n\n"
        f"🛒 Корзина доступна внизу каждого товара",
        parse_mode="Markdown"
    )
    
    # Показываем товары
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
    """Добавляет товар в корзину"""
    product_id = int(call.data.split("_")[1])
    
    # Находим товар
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
    
    # Создаем корзину
    if user_id not in carts:
        carts[user_id] = {}
    
    # Добавляем товар
    if product_id in carts[user_id]:
        carts[user_id][product_id]['qty'] += 1
    else:
        carts[user_id][product_id] = {
            'name': product['name'],
            'price': product['price'],
            'qty': 1
        }
    
    # Подсчитываем количество товаров в корзине
    total_items = sum(item['qty'] for item in carts[user_id].values())
    
    await call.answer(
        f"✅ {product['name']} добавлен!\n"
        f"📦 В корзине: {total_items} товар(ов)",
        show_alert=True
    )

@dp.callback_query(F.data == "cart")
async def view_cart(call: CallbackQuery):
    """Показывает корзину"""
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    
    if not cart:
        await call.message.edit_text(
            "🛒 *Корзина пуста*\n\n"
            "Добавьте товары из каталога",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return
    
    total = 0
    total_items = 0
    text = "🛒 *Ваша корзина:*\n\n"
    
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"• {item['name']}\n"
        text += f"  {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
        total_items += item['qty']
    
    text += f"📦 *Всего товаров:* {total_items} шт.\n"
    text += f"💰 *Итого:* {total} руб."
    
    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=cart_buttons()
    )
    await call.answer()

@dp.callback_query(F.data == "clear")
async def clear_cart(call: CallbackQuery):
    """Очищает корзину"""
    carts[call.from_user.id] = {}
    await call.message.edit_text(
        "🗑 *Корзина очищена!*\n\n"
        "Добавьте новые товары в каталоге",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery):
    """Оформляет заказ"""
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    
    if not cart:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    total_items = sum(item['qty'] for item in cart.values())
    
    # Сохраняем заказ (здесь можно добавить отправку в чат селлера)
    
    # Очищаем корзину
    carts[user_id] = {}
    
    await call.message.edit_text(
        f"✅ *Заказ оформлен!*\n\n"
        f"📦 Товаров: {total_items} шт.\n"
        f"💰 Сумма: {total} руб.\n\n"
        f"Скоро с вами свяжется менеджер для подтверждения.\n\n"
        f"Спасибо за покупку! 🐕",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    """Информация о магазине"""
    text = """🐕 *VetProfil - ветеринарная аптека*

📦 *Мы предлагаем:*
• Бравекто (все размеры)
• Нексгард
• Симпарика
• Лекарства и витамины

🚚 *Доставка:*
• Озон
• Wildberries
• СДЭК
• Яндекс Доставка

💊 *Все препараты сертифицированы*

🛒 *Корзина всегда доступна* - нажмите кнопку внизу"""
    
    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=about_kb()
    )
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    """Возврат в главное меню"""
    await call.message.edit_text(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "✅ Оригинальные препараты\n"
        "🚚 Доставка по всей России\n\n"
        "🛒 *Корзина всегда под рукой*",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

async def main():
    print("🚀 Бот VetProfil запущен!")
    print("🛒 Корзина теперь всегда видна!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
