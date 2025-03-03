from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# Замените на ваш токен
TOKEN = '7669430549:AAGbl6A3A8lFcSZVrkcwg409np9XpwjTdK8'

# Замените на URL вашего веб-приложения
WEB_APP_URL = 'https://sub.mykillwiki.ru/index.html'

async def start(update, context):
    # Получаем информацию о пользователе
    user = update.message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    # Выводим информацию о пользователе в консоль
    print(f"User entered the app: ID={user_id}, Username={username}, First Name={first_name}, Last Name={last_name}")

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