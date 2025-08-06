import telebot
import os
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

bad_words = ['کص', 'کیر', 'سیک']
link_pattern = re.compile(r'(http|https|t.me|telegram.me|www\.)')

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for new_member in message.new_chat_members:
        bot.send_message(message.chat.id, f"سلام {new_member.first_name} خوش اومدی به گروه!")

@bot.message_handler(func=lambda message: True)
def auto_reply_and_moderate(message):
    text = message.text
    if not text:
        return

    text_lower = text.lower()

    # پاسخ به کلمات خاص
    if any(word in text_lower for word in ['berlin', 'برلین']):
        bot.reply_to(message, "جانک عشقم بگو")
        return

    if 'سلام' in text_lower:
        bot.reply_to(message, "سلام عزیزم!")
        return

    if 'بای' in text_lower:
        bot.reply_to(message, "بای بای!")
        return

    # فیلتر کلمات بد
    for word in bad_words:
        if word in text_lower:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"{message.from_user.first_name} لطفا از کلمات نامناسب استفاده نکنید.")
            except Exception as e:
                print(f"خطا در حذف پیام: {e}")
            return

    # فیلتر لینک‌ها
    if link_pattern.search(text_lower):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"{message.from_user.first_name} ارسال لینک در این گروه ممنوع است.")
        except Exception as e:
            print(f"خطا در حذف پیام: {e}")
        return

print("ربات مدیریت گروه روشن شد...")
bot.infinity_polling()