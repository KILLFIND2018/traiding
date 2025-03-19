from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler
import mysql.connector

TOKEN = ''
WEB_APP_URL = ''

MYSQL_CONFIG = {
    'user': '',
    'password': '',
    'host': '',
    'database': '',
    'raise_on_warnings': True
}

async def start(update, context):
    user = update.message.from_user
    user_id = str(user.id)  # Приводим к строке для совместимости с Flask
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    print(f"User entered the app: ID={user_id}, Username={username}, First Name={first_name}, Last Name={last_name}")

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT * FROM user_progress WHERE user_id = %s", (user_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            # Добавляем пользователя в user_progress
            query = """
                INSERT INTO user_progress (user_id, username, first_name, last_name, balance, total_generation, progression_factor, last_updated, is_active)
                VALUES (%s, %s, %s, %s, 0, 11, 1.0, NOW(), 0)
            """
            cursor.execute(query, (user_id, username, first_name, last_name))
            
            # Добавляем бонусный "Older PC" в inventory
            cursor.execute("""
                INSERT INTO inventory (user_id, item_name, generation_per_hour)
                VALUES (%s, %s, %s)
            """, (user_id, "Older PC", 10))
            
            print(f"New user ID {user_id} added to the database with Older PC.")
        else:
            print(f"User ID {user_id} already exists in the database.")

        connection.commit()
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

    web_app_url = WEB_APP_URL.format(user_id=user_id)
    keyboard = [[InlineKeyboardButton("Open Web App", web_app={'url': web_app_url})]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Welcome to Crypto Tycoon Simulator! Open the web app:', reply_markup=reply_markup)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()