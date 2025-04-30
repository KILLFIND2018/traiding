from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
import mysql.connector
import requests
from config import TOKEN, WEB_APP_URL, MYSQL_CONFIG
import os

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

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            cursor.execute("""
                INSERT INTO user_progress 
                (user_id, username, first_name, last_name, balance, total_generation, is_active, last_updated)
                VALUES (%s, %s, %s, %s, 0, 6, 1, NOW())
            """, (user_id, username, first_name, last_name))

            cursor.execute("""
                INSERT INTO inventory (user_id, item_name, generation_per_hour)
                VALUES (%s, 'Older PC', 6)
            """, (user_id,))

            # Обработка реферала
            if referral_code:
                cursor.execute("""
                    SELECT user_id 
                    FROM referrals 
                    WHERE referral_code = %s AND used_by IS NULL
                    FOR UPDATE
                """, (referral_code,))
                result = cursor.fetchone()

                if result and result[0] != user_id:
                    referrer_id = result[0]
                    cursor.execute("""
                        UPDATE referrals 
                        SET used_by = %s, used_at = NOW() 
                        WHERE referral_code = %s
                    """, (user_id, referral_code))
                    cursor.execute("""
                        INSERT INTO inventory (user_id, item_name, generation_per_hour)
                        VALUES (%s, 'Macbook', 50)
                    """, (referrer_id,))
                    cursor.execute("""
                        UPDATE user_progress 
                        SET total_generation = total_generation + 50 
                        WHERE user_id = %s
                    """, (referrer_id,))
                    cursor.execute("""
                        INSERT INTO rewards (user_id, item_name)
                        VALUES (%s, 'Macbook')
                    """, (referrer_id,))
            connection.commit()

            try:
                requests.post('http://localhost:5000/start', json={'user_id': user_id})
            except Exception as e:
                print(f"Ошибка API: {e}")
    except mysql.connector.Error as err:
        print(f"Ошибка БД: {err}")
    finally:
        cursor.close()
        connection.close()

    # Отправка изображения
    # Отправка изображения
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "static", "start_image.png")
    try:
        await update.message.reply_photo("static/start_image.png")
    except Exception as e:
        print(f"Ошибка изображения: {e}")

    # Отправка текста и клавиатуры
    web_app_url = WEB_APP_URL.format(user_id=user_id)
    keyboard = [
        [InlineKeyboardButton("Learn About Tables", callback_data='learn_tables'),
         InlineKeyboardButton("Tycoon Simulator", web_app={'url': web_app_url})],
        [InlineKeyboardButton("Social Media", callback_data='social_media'),
         InlineKeyboardButton("About Tycoon", callback_data='about_tycoon')],
        [InlineKeyboardButton("Buy Coins with Stars", callback_data='buy_coins')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = """
🌟 *Welcome, Dear User, to Tycoon Simulator!* 🌟

This is your gateway to earning money in exciting and innovative ways! The more of us there are and the more active our community, the greater your potential earnings. At this stage of the project launch, you have *three unique ways to earn*:

1️⃣ *Be in the Top 25 Players* – Compete to secure a spot among the best and share in the prize pool!
2️⃣ *Sell NFT Items* – Starting in Season 2, trade exclusive NFT items on the Bybit NFT marketplace.
3️⃣ *Token Listing* – At the end of Season 3, our token will be listed. The more coins you collect, the bigger your rewards!

Let’s be clear: this is *not* another Hamster Kombat. Tycoon Simulator is a serious platform designed for real earnings. The logic is simple – *the more engagement and activity, the higher your profits*, as earnings are generated from advertising revenue. We, the creators, take only a small percentage.

If you’re ready to dive in, press *Start*, then *Tycoon Simulator* to begin your tutorial and explore the project! 🚀
"""
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'buy_coins':
        prices = [LabeledPrice("100 Coins", 10 * 100)]
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Buy 100 Coins",
            description="Purchase 100 coins for 10 Telegram Stars",
            payload=f"buy_coins_{query.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="buy-coins"
        )
    elif query.data == 'learn_tables':
        await query.message.reply_text("Tables are amazing! They hold your stuff, meals, and dreams!")
    elif query.data == 'about_tycoon':
        await query.message.reply_text(
            "Tycoon is your ultimate platform for discovering unique tables and furniture! "
            "We're passionate about quality, design, and creating opportunities for our community to earn through Tycoon Simulator."
        )
    elif query.data == 'social_media':
        social_keyboard = [
            [InlineKeyboardButton("Twitter (X)", url="https://x.com/tycoonempiretg"),
             InlineKeyboardButton("Reddit", url="https://reddit.com/r/tycoonsimulator")],
            [InlineKeyboardButton("Our Website", url="https://tycoonsimulator.com")],
        ]
        await query.message.reply_text("Follow us on social media!", reply_markup=InlineKeyboardMarkup(social_keyboard))

async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_coins_"):
        await context.bot.answer_pre_checkout_query(query.id, ok=True)
    else:
        await context.bot.answer_pre_checkout_query(query.id, ok=False, error_message="Invalid payment data")

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
            new_balance = result[0] + amount
            cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))
            connection.commit()
            await update.message.reply_text(f"Success! You bought 100 coins. New balance: {new_balance}")
        else:
            await update.message.reply_text("Error: User not found.")
    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        await update.message.reply_text("An error occurred during payment.")
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