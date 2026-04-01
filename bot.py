import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# Берем токен из переменных окружения (безопасно)
BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Товары (категории и товары)
PRODUCTS = {
    "antiparasitic": [  # Категория "От блох и клещей"
        {"id": 1, "name": "Бравекто 2-4.5 кг", "price": 1850, "desc": "Защита 12 недель\nДля собак 2-4.5 кг"},
        {"id": 2, "name": "Бравекто 4.5-10 кг", "price": 2150, "desc": "Защита 12 недель\nДля собак 4.5-10 кг"},
        {"id": 3, "name": "Бравекто 10-20 кг", "price": 2450, "desc": "Защита 12 недель\nДля собак 10-20 кг"},
        {"id": 4, "name": "Нексгард 4-10 кг", "price": 1950, "desc": "Защита 1 месяц\n3 таблетки"},
    ],
    "medicine": [  # Категория "Лекарства"
        {"id": 5, "name": "Стоп-зуд", "price": 890, "desc": "От аллергии\n20 таблеток"},
    ],
    "vitamins": [  # Категория "Витамины"
        {"id": 6, "name": "Глюкозамин", "price": 1250, "desc": "Для суставов\n90 таблеток"},
        {"id": 7, "name": "Омега-3", "price": 980, "desc": "Для шерсти\n60 капсул"},
    ]
}

# Корзина (хранится в памяти)
carts = {}

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])

def categories_menu():
    """Меню категорий"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 От блох и клещей", callback_data="cat_antiparasitic")],
        [InlineKeyboardButton(text="💊 Лекарства", callback_data="cat_medicine")],
        [InlineKeyboardButton(text="🍖 Витамины", callback_data="cat_vitamins")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

def product_buttons(product_id):
    """Кнопки товара"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
    ])

def cart_buttons():
    """Кнопки корзины"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear")],
        [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")]
    ])

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def start(message: Message):
    """Приветствие при старте"""
    await message.answer(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    """Показывает категории"""
    await call.message.edit_text(
        "📁 *Выберите категорию:*",
        parse_mode="Markdown",
        reply_markup=categories_menu()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_products(call: CallbackQuery):
    """Показывает товары в категории"""
    category = call.data.split("_")[1]  # берем категорию из callback
    products = PRODUCTS.get(category, [])
    
    if not products:
        await call.message.edit_text("😕 Товаров в этой категории пока нет")
        return
    
    for product in products:
        text = f"*{product['name']}*\n{product['desc']}\n💰 {product['price']} руб."
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
    
    # Создаем корзину для пользователя, если её нет
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
    
    await call.answer(f"✅ {product['name']} добавлен в корзину!", show_alert=True)

@dp.callback_query(F.data == "cart")
async def view_cart(call: CallbackQuery):
    """Показывает корзину"""
    user_id = call.from_user.id
    cart = carts.get(user_id, {})
    
    if not cart:
        await call.message.edit_text(
            "🛒 *Корзина пуста*\n\nДобавьте товары из каталога",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return
    
    total = 0
    text = "🛒 *Ваша корзина:*\n\n"
    
    for item in cart.values():
        subtotal = item['price'] * item['qty']
        text += f"• {item['name']}\n"
        text += f"  {item['price']} руб. × {item['qty']} = {subtotal} руб.\n\n"
        total += subtotal
    
    text += f"💰 *Итого: {total} руб.*"
    
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
        "🗑 Корзина очищена!",
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
    
    # Очищаем корзину после заказа
    carts[user_id] = {}
    
    await call.message.edit_text(
        f"✅ *Заказ оформлен!*\n\n"
        f"💰 Сумма: {total} руб.\n\n"
        f"Скоро с вами свяжется менеджер для подтверждения.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    """Возврат в главное меню"""
    await call.message.edit_text(
        "🐕 *VetProfil - ветеринарная аптека*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await call.answer()

# ========== ЗАПУСК ==========
async def main():
    print("🚀 Бот VetProfil запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
