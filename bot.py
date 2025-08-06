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
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        result = response.json()
        # مدل DialoGPT پاسخ را به صورت لیست و دیکشنری می‌دهد
        if isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text']
        # برخی مدل‌ها پاسخ را متفاوت می‌دهند؛ اینجا بررسی ساده است
        return "متأسفم، پاسخی دریافت نشد."
    else:
        return f"خطا در ارتباط با API: {response.status_code}"

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_text = message.text
    reply = query_hf_api(user_text)
    bot.reply_to(message, reply)

print("ربات شروع به کار کرد...")
bot.infinity_polling()