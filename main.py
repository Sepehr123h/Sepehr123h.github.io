import telebot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # گرفتن توکن از محیط امن Render

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام برلین 🚀 رباتت به GitHub و Render وصله!")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, f"گفتی: {message.text}")

print("ربات روشن شد...")
bot.infinity_polling()