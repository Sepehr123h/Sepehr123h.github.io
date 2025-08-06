import os
import telebot
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

bot = telebot.TeleBot(BOT_TOKEN)

def query_hf_api(text):
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text']
        return "متأسفم، پاسخی دریافت نشد."
    else:
        return "خطا در ارتباط با API."

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_text = message.text
    reply = query_hf_api(user_text)
    bot.reply_to(message, reply)

print("ربات شروع به کار کرد...")
bot.infinity_polling()