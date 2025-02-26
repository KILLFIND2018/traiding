

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# Замените на ваш токен
TOKEN = ''

# Замените на URL вашего веб-приложения
WEB_APP_URL = 'https://sub.mykillwiki.ru/index.html'

async def start(update, context):
    keyboard = [[InlineKeyboardButton("Open Web App", web_app={'url': WEB_APP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
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
