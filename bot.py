from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
import mysql.connector
import requests
import os
from config import TOKEN, WEB_APP_URL, MYSQL_CONFIG


import re

user_wallet_entry_mode = set()


TON_ADDRESS_RE = re.compile(r'^[A-Za-z0-9_-]{48,64}$')

def is_valid_ton_address(addr: str) -> bool:
    return bool(TON_ADDRESS_RE.match(addr))

# ID администратора (замени на свой Telegram ID)
ADMIN_USER_ID = "8170805217"

async def start(update, context):
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username
    first_name = user.first_name or "Player"
    last_name = user.last_name
    referral_code = context.args[0] if context.args else None

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

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

    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "static", "start_image.png")
    try:
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(photo)
    except Exception as e:
        print(f"Ошибка изображения: {e}")

    web_app_url = WEB_APP_URL.format(user_id=user_id)
    keyboard = [
        [InlineKeyboardButton("Tycoon Simulator", web_app={'url': web_app_url})],
        [
            InlineKeyboardButton("X", url="https://x.com/tycoonempiretg?s=21"),
            InlineKeyboardButton("TikTok", url="https://www.tiktok.com/@size.kong?_t=ZN-8wGhFAZWYUQ&_r=1"),
            InlineKeyboardButton("Website", url="https://www.tycoonsimulatortg.com"),
            InlineKeyboardButton("Reddit", url="https://www.reddit.com/u/CryptoEmpireTycoon/s/TCYZmkSSwn"),
        ],
        [InlineKeyboardButton("How to Earn TON", callback_data='how_to_earn_ton')],
        [InlineKeyboardButton("Support", callback_data='support')],
        [InlineKeyboardButton("About Us", callback_data='about_us')],
        [InlineKeyboardButton("🔗 Link TON Wallet", callback_data='link_wallet')],
        [InlineKeyboardButton("Restart", callback_data='restart')],
        [InlineKeyboardButton("Buy Coins with Stars", callback_data='buy_coins')],
]

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"Welcome to Tycoon Simulator, {first_name}! 🎉\n"
        "This exciting project is designed to help you earn in the TON ecosystem. Scale your empire by making purchases, playing in our simulator, and climbing the ranks on our leaderboard. Enjoy a dynamic in-game economy with multiple earning opportunities—both virtual currency and real TON!\n\n"
        "Learn more about earning TON on our website or via the 'How to Earn TON' button. After completing the in-game tutorial, dive into the action and test your luck! We also feature an item marketplace, with plans to launch items as NFTs on a marketplace by the end of the season. At season’s end (90 days), your balance will convert to TON, and we’ll introduce the Tycoon token listing.\n\n"
        "Get started now and build your legacy! 🚀"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    # Клавиатура с кнопкой "Назад"
    back_button = [[InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]]
    back_markup = InlineKeyboardMarkup(back_button)

    if query.data == 'buy_coins':
        prices = [LabeledPrice("1000 Stars", 1000 * 100)]
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Buy 750,000 Tokens",
            description="Purchase 750,000 tokens for 1000 Telegram Stars",
            payload=f"buy_coins_{query.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="buy-tokens"
        )
    elif query.data == 'how_to_earn_ton':
        await query.edit_message_text(
            "Hello, dear player! 🎯 By clicking this, you're interested in earning real rewards! Our app offers exciting opportunities, and with patience, you can profit without investment by waiting until the season ends. After the tutorial, dive into our mini-games with the following win chances:\n\n"
            "- Sector 1 (10%): 3x tokens + 0.05 TON\n"
            "- Sector 2 (15%): 100,000 tokens + 1 TON\n"
            "- Sector 3 (25%): 1,000 tokens + Bonus Chance\n"
            "- Sector 4 (5%): Drinking Water Dispenser + 1.2 TON\n"
            "- Sector 5 (25%): 2,000 tokens + Bonus Chance\n"
            "- Sector 6 (10%): 2x tokens + 0.07 TON\n"
            "- Sector 7 (5%): Humanoid Robot + 0.9 TON\n"
            "- Sector 8 (5%): 10,000 tokens + Bonus Chance\n\n"
            "For real TON, try the premium Roulette layer—spend TON for a chance to win up to 1.2 TON. With persistence, we’ll convert your balance to TON after the 90-day season. Stay tuned for frequent contests and events with amazing prizes!",
            reply_markup=back_markup
        )
    elif query.data == 'support':
        await query.edit_message_text(
            "Need help? Contact us at @TycoonSim for assistance!",
            reply_markup=back_markup
        )
    elif query.data == 'about_us':
        await query.edit_message_text(
            "Hello, dear player! 👋 We’ve spent six months crafting Tycoon Simulator with a vision to expand based on your support. Follow our social media, stay active, and help us reach the Bybit NFT marketplace! Every item you buy is tied to your Telegram account, paving the way for future cryptocurrency sales. We wish you luck and promise frequent contests and events with amazing rewards!",
            reply_markup=back_markup
        )
    elif query.data == 'restart':
        await context.bot.send_message(chat_id=query.message.chat_id, text="/start")
    elif query.data == 'link_wallet':
        user_id = query.from_user.id
        user_wallet_entry_mode.add(user_id)
        await query.message.reply_text("📨 Пришлите ваш TON-адрес (начинается с EQ или UQ...)")

    elif query.data == 'back_to_menu':
        user = query.from_user
        first_name = user.first_name or "Player"
        web_app_url = WEB_APP_URL.format(user_id=user.id)
        keyboard = [
            [InlineKeyboardButton("Tycoon Simulator", web_app={'url': web_app_url})],
            [
                InlineKeyboardButton("X", url="https://x.com/tycoonempiretg?s=21"),
                InlineKeyboardButton("TikTok", url="https://www.tiktok.com/@size.kong?_t=ZN-8wGhFAZWYUQ&_r=1"),
                InlineKeyboardButton("Website", url="https://www.tycoonsimulatortg.com"),
                InlineKeyboardButton("Reddit", url="https://www.reddit.com/u/CryptoEmpireTycoon/s/TCYZmkSSwn"),
            ],
            [InlineKeyboardButton("How to Earn TON", callback_data='how_to_earn_ton')],
            [InlineKeyboardButton("Support", callback_data='support')],
            [InlineKeyboardButton("About Us", callback_data='about_us')],
            [InlineKeyboardButton("🔗 Link TON Wallet", callback_data='link_wallet')],
            [InlineKeyboardButton("Restart", callback_data='restart')],
            [InlineKeyboardButton("Buy Coins with Stars", callback_data='buy_coins')],
]

        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome_text = (
            f"Welcome to Tycoon Simulator, {first_name}! 🎉\n"
            "This exciting project is designed to help you earn in the TON ecosystem. Scale your empire by making purchases, playing in our simulator, and climbing the ranks on our leaderboard. Enjoy a dynamic in-game economy with multiple earning opportunities—both virtual currency and real TON!\n\n"
            "Learn more about earning TON on our website or via the 'How to Earn TON' button. After completing the in-game tutorial, dive into the action and test your luck! We also feature an item marketplace, with plans to launch items as NFTs on a marketplace by the end of the season. At season’s end (90 days), your balance will convert to TON, and we’ll introduce the Tycoon token listing.\n\n"
            "Get started now and build your legacy! 🚀"
        )
        await query.edit_message_text(welcome_text, reply_markup=reply_markup)

async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("buy_coins_"):
        await context.bot.answer_pre_checkout_query(query.id, ok=True)
    else:
        await context.bot.answer_pre_checkout_query(query.id, ok=False, error_message="Invalid payment data")

async def successful_payment(update, context):
    payment = update.message.successful_payment
    user_id = payment.invoice_payload.split("_")[2]
    amount = 750000
    stars_amount = 1000

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            new_balance = result[0] + amount
            cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))
            # Клавиатура с кнопкой "Назад" после успешной оплаты
            back_button = [[InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]]
            back_markup = InlineKeyboardMarkup(back_button)
            await update.message.reply_text(
                f"Success! You bought 750,000 tokens. New balance: {new_balance}",
                reply_markup=back_markup
            )
        else:
            await update.message.reply_text("Error: User not found.")
            return

        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (ADMIN_USER_ID,))
        admin_result = cursor.fetchone()
        if admin_result:
            admin_new_balance = admin_result[0] + stars_amount
            cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (admin_new_balance, ADMIN_USER_ID))
        else:
            cursor.execute("""
                INSERT INTO user_progress 
                (user_id, username, first_name, last_name, balance, total_generation, is_active, last_updated)
                VALUES (%s, %s, %s, %s, %s, 0, 1, NOW())
            """, (ADMIN_USER_ID, "admin", "Admin", "User", stars_amount))

        connection.commit()

        try:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"New transaction! User {user_id} paid 1000 Stars. You received {stars_amount} tokens. Your new balance: {admin_new_balance if admin_result else stars_amount}"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления администратору: {e}")

    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        await update.message.reply_text("An error occurred during payment.")
    finally:
        cursor.close()
        connection.close()

async def handle_webapp_data(update, context):
    if update.message.web_app_data:
        data = update.message.web_app_data.data
        if data.startswith("spin_ton_"):
            tx = data.split("_", 2)[2]
            user_id = str(update.effective_user.id)

            try:
                requests.post(
                    'https://tycoonofficial.com/confirm_ton_payment',
                    json={'transaction_id': tx, 'user_id': user_id},
                    timeout=5
                )
            except Exception as e:
                print("Error notifying Flask of TON payment:", e)
            
            # Отправляем инвойс
            await context.bot.send_invoice(
                chat_id=update.message.chat_id,
                title="Spin the Wheel",
                description="Pay 0.01 TON to spin the wheel",
                payload=f"spin_ton_{tx}",
                provider_token="",  # Пустое для TON-платежей
                currency="TON",
                prices=[LabeledPrice("Spin Cost", 10000000)]  # 0.01 TON = 10,000,000 nanoTON
            )

# Запрос адреса
async def ask_wallet(update, context):
    user_id = update.effective_user.id
    user_wallet_entry_mode.add(user_id)
    await update.message.reply_text("📨 Пришлите ваш TON-адрес (начинается с EQ или UQ...)")


# Сохранение TON-адреса
async def save_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # int — корректно для BIGINT в MySQL
    text = update.message.text.strip()

    print(f"[DEBUG] save_wallet: user_id={user_id}, message='{text}'")

    if user_id not in user_wallet_entry_mode:
        print("[DEBUG] Not in entry mode, skipping.")
        return

    user_wallet_entry_mode.remove(user_id)

    if not is_valid_ton_address(text):
        await update.message.reply_text("❌ Это не похоже на корректный TON-адрес.")
        return

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute(
            "REPLACE INTO user_wallets (user_id, ton_address) VALUES (%s, %s)",
            (user_id, text)
        )
        connection.commit()

        # Проверка, что адрес действительно записался
        cursor.execute("SELECT ton_address FROM user_wallets WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        print(f"[DEBUG] DB confirmation: {row}")

        await update.message.reply_text(f"✅ Адрес сохранён: `{text}`", parse_mode='Markdown')

    except mysql.connector.Error as e:
        print(f"[ERROR] MySQL error: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении адреса в базу данных.")

    finally:
        cursor.close()
        connection.close()



def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    application.add_handler(CommandHandler("wallet", ask_wallet))
    application.add_handler(MessageHandler(filters.TEXT, save_wallet))
    application.run_polling()



if __name__ == '__main__':
    main()
