from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler
import mysql.connector

# Замените на ваш токен
TOKEN = ''

# Замените на URL вашего веб-приложения
WEB_APP_URL = 'https://sub.mykillwiki.ru/index.html'

# Настройки подключения к базе данных MySQL
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'telegram_bot',
    'raise_on_warnings': True
}

async def start(update, context):
    # Получаем информацию о пользователе
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    # Выводим информацию о пользователе в консоль
    print(f"User entered the app: ID={user_id}, Username={username}, First Name={first_name}, Last Name={last_name}")

    # Записываем user_id и username в базу данных
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Вставляем user_id и username в таблицу user_progress
        query = "INSERT INTO user_progress (user_id, username) VALUES (%s, %s)"
        cursor.execute(query, (user_id, username))

        connection.commit()
        cursor.close()
        connection.close()

        print(f"User ID {user_id} and username {username} successfully saved to the database.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")

    # Создаем кнопку для открытия веб-приложения
    keyboard = [[InlineKeyboardButton("Open Web App", web_app={'url': WEB_APP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопкой
    await update.message.reply_text('Please open the web app:', reply_markup=reply_markup)

def main():
    # Создаем Application
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()