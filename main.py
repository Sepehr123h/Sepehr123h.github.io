import telebot
import os
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

bad_words = [
    'لعنت', 'کثافت', 'بی‌ادب', 'بی‌جنبه', 'کسخل', 'گوه', 'هرزه', 'حرومزاده',
    'مزخرف', 'مزخرف‌گو', 'دلقک', 'احمق', 'خر', 'بی‌فرهنگ', 'نفهم', 'بی‌عقل',
    'آدم‌نما', 'مرده‌خور', 'دماغ‌کلفت', 'عوضی', 'خرخون', 'جلف', 'شاعر',
    'سیک', 'کیر', 'کص', 'حرومزاده'
]

call_words = ['berlin', 'برلین']

link_pattern = re.compile(r'(http|https|t\.me|telegram\.me|www\.)')

response_msgs = [
    "جانم عشقم",
    "چی شده",
    "چته",
    "ها",
    "بگو",
    "برو پیویش"
]

warnings = {}
max_warnings = 3

# دیکشنری برای ذخیره شاخص پاسخ بعدی برای هر چت
chat_response_index = {}

def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        bot.send_message(message.chat.id, f"سلام {member.first_name} خوش اومدی به گروه 🌟")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'audio'])
def handle_messages(message):
    text = message.text
    if not text:
        return

    text_lower = text.lower()
    chat_id = message.chat.id

    # پاسخ چرخشی به صدا زدن Berlin و سپهر
    if any(word in text_lower for word in call_words) or 'سپهر' in text_lower:
        index = chat_response_index.get(chat_id, 0)
        bot.send_message(chat_id, response_msgs[index])
        index = (index + 1) % len(response_msgs)
        chat_response_index[chat_id] = index
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
            user_id = message.from_user.id
            warnings[user_id] = warnings.get(user_id, 0) + 1
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"{message.from_user.first_name} اخطار {warnings[user_id]}/{max_warnings}")
                if warnings[user_id] >= max_warnings:
                    bot.kick_chat_member(message.chat.id, user_id)
                    bot.send_message(message.chat.id, f"{message.from_user.first_name} به دلیل تخلف بن شد 🚫")
            except:
                pass
            return

    # فیلتر لینک
    if link_pattern.search(text_lower):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"{message.from_user.first_name} ارسال لینک ممنوع است ❌")
        except:
            pass
        return

print("ربات مدیریت گروه فول آپشن روشن شد...")
bot.infinity_polling()