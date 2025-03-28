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
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            query = """
                INSERT INTO user_progress (user_id, username, first_name, last_name, balance, total_generation, progression_factor, last_updated, is_active)
                VALUES (%s, %s, %s, %s, 0, 10, 0, NOW(), 0)
            """
            cursor.execute(query, (user_id, username, first_name, last_name))
            cursor.execute("""
                INSERT INTO inventory (user_id, item_name, generation_per_hour)
                VALUES (%s, %s, %s)
            """, (user_id, "Older PC", 10))
            connection.commit()

            if referral_code:
                cursor.execute("SELECT user_id FROM referrals WHERE referral_code = %s AND used_by IS NULL", (referral_code,))
                result = cursor.fetchone()
                if result:
                    referrer_id = result[0]
                    if referrer_id != user_id:
                        cursor.execute("""
                            UPDATE referrals 
                            SET used_by = %s, used_at = NOW()
                            WHERE referral_code = %s
                        """, (user_id, referral_code))
                        cursor.execute("""
                            INSERT INTO inventory (user_id, item_name, generation_per_hour)
                            VALUES (%s, %s, %s)
                        """, (referrer_id, "Macbook", 50))
                        # Добавляем запись в таблицу rewards
                        cursor.execute("""
                            INSERT INTO rewards (user_id, item_name)
                            VALUES (%s, %s)
                        """, (referrer_id, "Macbook"))
                        connection.commit()
                        print(f"Пользователь {user_id} использовал реферальный код {referral_code}. Реферер {referrer_id} получил Macbook.")

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
    finally:
        cursor.close()
        connection.close()


    web_app_url = WEB_APP_URL.format(user_id=user_id)
    keyboard = [
        [InlineKeyboardButton("Открыть Web App", web_app={'url': web_app_url})],
        [InlineKeyboardButton("Купить монеты за Stars", callback_data='buy_coins')],
        [InlineKeyboardButton("Пригласить друга", callback_data='invite_friend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        'Добро пожаловать в Crypto Tycoon Simulator! Выберите действие:',
        reply_markup=reply_markup
    )

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
    elif query.data == 'invite_friend':
        await query.answer()
        try:
            connection = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = connection.cursor()
            cursor.execute("SELECT referral_code FROM referrals WHERE user_id = %s AND used_by IS NULL", (str(query.from_user.id),))
            result = cursor.fetchone()
            
            referral_code = result[0] if result else None
            if not referral_code:
                response = requests.post('http://localhost:5000/generate_referral', 
                                      json={'user_id': str(query.from_user.id)})
                data = response.json()
                if data['status'] == 'success':
                    referral_code = data['referral_code']
            
            referral_link = f"https://t.me/CTSimulatorBot?start={referral_code}"
            await query.message.reply_text(f"Поделитесь этой ссылкой с другом:\n{referral_link}")
            
        except Exception as e:
            await query.message.reply_text(f"Ошибка при генерации ссылки: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

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