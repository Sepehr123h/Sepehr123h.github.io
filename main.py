import os
import telebot
from flask import Flask, request
import requests

# گرفتن توکن‌ها از متغیرهای محیطی Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# لینک مدل Hugging Face
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

# ساخت بات تلگرام
bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# تابع درخواست از Hugging Face
def query_hf_api(text):
    payload = {"inputs": text}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            if isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            return "🤖 پاسخ مناسبی پیدا نشد."
        else:
            return f"❌ خطا: {response.status_code}"
    except Exception as e:
        return f"🚫 خطا در ارتباط با API: {e}"

# هندلر پیام‌ها
@bot.message_handler(func=lambda message: True)
def reply_all(message):
    user_text = message.text
    reply = query_hf_api(user_text)
    bot.reply_to(message, reply)

# مسیر Webhook
@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# مسیر اصلی برای تست
@server.route("/")
def index():
    return "✅ Berlin Bot is running!", 200

# اجرای سرور
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://sepehr123h-github-io.onrender.com/{BOT_TOKEN}")
    server.run(host="0.0.0.0", port=10000)