@dp.message(OrderForm.waiting_for_pickup_point)
async def get_pickup_point(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    cart = carts.get(user_id, {})
    
    # Получаем username пользователя
    user = message.from_user
    username = user.username if user.username else "Не указан"
    
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
    order_text += f"📱 Телефон: {data['phone']}\n"
    order_text += f"👤 Username: @{username}\n"
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
        f"📱 {data['phone']}\n"
        f"🚚 {data['delivery'].upper()}\n"
        f"🏠 {message.text}\n"
        f"💰 {total} руб.\n\n"
        f"В ближайшее время с Вами свяжутся для согласования заказа.\n\n"
        f"🐕 Спасибо за покупку!\n\n"
        f"⭐ Оставьте отзыв в разделе 'ОТЗЫВЫ'",
        reply_markup=main_menu()
    )
