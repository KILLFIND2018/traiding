from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
import mysql.connector

# Токен вашего бота
TOKEN = ''
WEB_APP_URL = ''

# Конфигурация MySQL
MYSQL_CONFIG = {
    'user': '',
    'password': '',
    'host': '',
    'database': '',
    'raise_on_warnings': True
}

async def start(update, context):
    """Обработчик команды /start"""
    user = update.message.from_user
    user_id = str(user.id)  # Приводим к строке для совместимости с Flask
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    print(f"Пользователь вошел в приложение: ID={user_id}, Username={username}, Имя={first_name}, Фамилия={last_name}")

    # Подключение к базе данных
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            # Добавляем нового пользователя
            query = """
                INSERT INTO user_progress (user_id, username, first_name, last_name, balance, total_generation, progression_factor, last_updated, is_active)
                VALUES (%s, %s, %s, %s, 0, 11, 1.0, NOW(), 0)
            """
            cursor.execute(query, (user_id, username, first_name, last_name))
            
            # Добавляем бонусный "Older PC" в инвентарь
            cursor.execute("""
                INSERT INTO inventory (user_id, item_name, generation_per_hour)
                VALUES (%s, %s, %s)
            """, (user_id, "Older PC", 10))
            
            print(f"Новый пользователь ID {user_id} добавлен в базу данных с Older PC.")
        else:
            print(f"Пользователь ID {user_id} уже существует в базе данных.")

        connection.commit()
    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
    finally:
        cursor.close()
        connection.close()

    # Создаем клавиатуру с кнопками
    web_app_url = WEB_APP_URL.format(user_id=user_id)
    keyboard = [
        [InlineKeyboardButton("Открыть Web App", web_app={'url': web_app_url})],
        [InlineKeyboardButton("Купить монеты за Stars", callback_data='buy_coins')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем приветственное сообщение
    await update.message.reply_text(
        'Добро пожаловать в Crypto Tycoon Simulator! Откройте приложение или купите монеты:',
        reply_markup=reply_markup
    )

async def handle_callback(update, context):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    if query.data == 'buy_coins':
        await query.answer()
        # Создаем счет для покупки 100 монет за 10 Stars
        prices = [LabeledPrice("100 монет", 10 * 100)]  # 10 Stars (цена в условных единицах, 100 = 1 Star)
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Купить 100 монет",
            description="Покупка 100 монет за 10 Telegram Stars",
            payload=f"buy_coins_{query.from_user.id}",  # Уникальный идентификатор покупки
            provider_token="",  # Оставляем пустым для Telegram Stars
            currency="XTR",  # Код валюты Telegram Stars
            prices=prices,
            start_parameter="buy-coins"
        )

async def precheckout_callback(update, context):
    """Предварительная проверка платежа"""
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_coins_"):
        await context.bot.answer_pre_checkout_query(query.id, ok=True)
    else:
        await context.bot.answer_pre_checkout_query(query.id, ok=False, error_message="Неверные данные платежа")

async def successful_payment(update, context):
    """Обработка успешного платежа"""
    payment = update.message.successful_payment
    user_id = payment.invoice_payload.split("_")[2]  # Извлекаем user_id из payload
    amount = 100  # Количество монет, добавляемых за покупку

    # Обновляем баланс пользователя в базе данных
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Получаем текущий баланс
        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            balance = result[0]
            new_balance = balance + amount

            # Обновляем баланс
            cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))
            connection.commit()
            print(f"Пользователь {user_id} успешно купил {amount} монет за Stars. Новый баланс: {new_balance}")

            # Уведомляем пользователя
            await update.message.reply_text(f"Успех! Вы купили 100 монет. Новый баланс: {new_balance}")
        else:
            print(f"Пользователь {user_id} не найден в базе данных.")
            await update.message.reply_text("Ошибка: Пользователь не найден.")
    except mysql.connector.Error as err:
        print(f"Ошибка базы данных при обновлении баланса: {err}")
        await update.message.reply_text("Ошибка при обработке покупки. Попробуйте позже.")
    finally:
        cursor.close()
        connection.close()

def main():
    """Основная функция запуска бота"""
    # Создаем приложение Telegram
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()