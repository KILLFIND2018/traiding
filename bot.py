from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
import mysql.connector
import requests
from config import TOKEN, WEB_APP_URL, MYSQL_CONFIG

async def start(update, context):
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    referral_code = context.args[0] if context.args else None

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверяем существование пользователя
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            # Создаем пользователя с генерацией 10 (от Older PC) и активируем генерацию
            query = """
                INSERT INTO user_progress 
                (user_id, username, first_name, last_name, balance, total_generation, is_active, last_updated)
                VALUES (%s, %s, %s, %s, 0, 6, 1, NOW())
            """
            cursor.execute(query, (user_id, username, first_name, last_name))

            # Добавляем стартовый предмет
            cursor.execute("""
                INSERT INTO inventory (user_id, item_name, generation_per_hour)
                VALUES (%s, 'Older PC', 6)
            """, (user_id,))

            # Обработка реферального кода
            if referral_code:
                # Проверяем код и блокируем строку
                cursor.execute("""
                    SELECT user_id 
                    FROM referrals 
                    WHERE referral_code = %s AND used_by IS NULL
                    FOR UPDATE
                """, (referral_code,))
                result = cursor.fetchone()

                if result and result[0] != user_id:
                    referrer_id = result[0]

                    # Помечаем код как использованный
                    cursor.execute("""
                        UPDATE referrals 
                        SET used_by = %s, used_at = NOW() 
                        WHERE referral_code = %s
                    """, (user_id, referral_code))

                    # Добавляем Macbook рефереру
                    cursor.execute("""
                        INSERT INTO inventory (user_id, item_name, generation_per_hour)
                        VALUES (%s, 'Macbook', 50)
                    """, (referrer_id,))

                    # Обновляем total_generation реферера
                    cursor.execute("""
                        UPDATE user_progress 
                        SET total_generation = total_generation + 50 
                        WHERE user_id = %s
                    """, (referrer_id,))

                    # Уведомление в rewards
                    cursor.execute("""
                        INSERT INTO rewards (user_id, item_name)
                        VALUES (%s, 'Macbook')
                    """, (referrer_id,))

            connection.commit()

            # Запускаем генерацию через API
            try:
                response = requests.post('http://localhost:5000/start', json={'user_id': user_id})
                if response.status_code != 200:
                    print(f"Ошибка запуска генерации для {user_id}")
            except Exception as e:
                print(f"API error: {e}")

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
    finally:
        cursor.close()
        connection.close()

    # Отправка интерфейса
    web_app_url = WEB_APP_URL.format(user_id=user_id)
    keyboard = [
        [InlineKeyboardButton("Открыть Web App", web_app={'url': web_app_url})],
        [InlineKeyboardButton("Купить монеты за Stars", callback_data='buy_coins')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Добро пожаловать!', reply_markup=reply_markup)

async def handle_callback(update, context):
    query = update.callback_query
    if query.data == 'buy_coins':
        await query.answer()
        prices = [LabeledPrice("100 монет", 10 * 100)]
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Купить 100 монет",
            description="Покупка 100 монет за 10 Telegram Stars",
            payload=f"buy_coins_{query.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="buy-coins"
        )

async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_coins_"):
        await context.bot.answer_pre_checkout_query(query.id, ok=True)
    else:
        await context.bot.answer_pre_checkout_query(query.id, ok=False, error_message="Неверные данные платежа")

async def successful_payment(update, context):
    payment = update.message.successful_payment
    user_id = payment.invoice_payload.split("_")[2]
    amount = 100

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            balance = result[0]
            new_balance = balance + amount
            cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))
            connection.commit()
            await update.message.reply_text(f"Успех! Вы купили 100 монет. Новый баланс: {new_balance}")
        else:
            await update.message.reply_text("Ошибка: Пользователь не найден.")
    except mysql.connector.Error as err:
        print(f"Ошибка базы данных при обновлении баланса: {err}")
        await update.message.reply_text("Ошибка при обработке покупки. Попробуйте позже.")
    finally:
        cursor.close()
        connection.close()

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    application.run_polling()

if __name__ == '__main__':
    main()