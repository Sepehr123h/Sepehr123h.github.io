from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# اینجا توکن ربات رو وارد کن (توکن رو از BotFather گرفتی)
TOKEN = '8438885501:AAFmdN6e8HzW6Xalwyjv3gGTzQxRQ9FkIC4'

# تابع شروع
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('سلام! من ربات تلگرام شما هستم.')

# تابع برای پاسخ به پیام‌ها
def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)

# تابع اصلی
def main() -> None:
    updater = Updater(TOKEN)

    # دستورات و پیام‌های مختلف
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))  # دستور /start
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))  # پاسخ به پیام‌ها

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()