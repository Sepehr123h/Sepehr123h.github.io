import telebot
from telebot import types
import os
import re
import json
import time
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

SETTINGS_FILE = 'settings.json'

default_settings = {
    'bad_words': ['لعنت', 'کثافت', 'کسخل', 'گوه', 'حرومزاده', 'سیک', 'کیر', 'کص'],
    'lock_links': True,
    'lock_media': False,
    'lock_sticker': False,
    'lock_gif': False,
    'min_account_days': 0,
    'spam_limit': 5,
    'admin_log_chat_id': None,
    'clean_join': True,
    'clean_pin': True
}

settings = {}
spam_tracker = {}

def load_settings():
    global settings
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except:
        settings = {}

def save_settings():
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

load_settings()

def ensure_group_settings(chat_id):
    if str(chat_id) not in settings:
        settings[str(chat_id)] = default_settings.copy()
        save_settings()

def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

link_pattern = re.compile(r'(http|https|t\.me|telegram\.me|www\.)')

# پنل مدیریت
def send_admin_panel(chat_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👁 مشاهده کلمات بد", callback_data="view_bad"),
        types.InlineKeyboardButton("➕ افزودن کلمه بد", callback_data="add_bad"),
        types.InlineKeyboardButton("➖ حذف کلمه بد", callback_data="remove_bad"),
        types.InlineKeyboardButton("🔗 قفل لینک", callback_data="toggle_links"),
        types.InlineKeyboardButton("🖼 قفل مدیا", callback_data="toggle_media"),
        types.InlineKeyboardButton("⚠ امنیت", callback_data="security"),
        types.InlineKeyboardButton("🧹 پاکسازی خودکار", callback_data="cleaning"),
        types.InlineKeyboardButton("📚 راهنما", callback_data="help"),
        types.InlineKeyboardButton("❌ خروج", callback_data="exit")
    )
    bot.send_message(chat_id, "🔧 پنل مدیریت گروه:", reply_markup=kb)

@bot.message_handler(commands=['panel'])
def panel_cmd(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "فقط ادمین‌ها اجازه دسترسی به پنل را دارند.")
        return
    ensure_group_settings(message.chat.id)
    send_admin_panel(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    ensure_group_settings(chat_id)
    group_settings = settings[str(chat_id)]

    if not is_admin(chat_id, user_id):
        bot.answer_callback_query(call.id, "شما ادمین نیستید!")
        return

    if call.data == "view_bad":
        words = group_settings['bad_words']
        bot.send_message(chat_id, "📝 کلمات بد:\n" + "\n".join(words))
        send_admin_panel(chat_id)

    elif call.data == "add_bad":
        msg = bot.send_message(chat_id, "کلمه بد جدید را بفرستید:")
        bot.register_next_step_handler(msg, add_bad_word)

    elif call.data == "remove_bad":
        kb = types.InlineKeyboardMarkup()
        for w in group_settings['bad_words']:
            kb.add(types.InlineKeyboardButton(w, callback_data=f"del_{w}"))
        kb.add(types.InlineKeyboardButton("انصراف", callback_data="cancel"))
        bot.send_message(chat_id, "یک کلمه برای حذف انتخاب کنید:", reply_markup=kb)

    elif call.data.startswith("del_"):
        word = call.data.replace("del_", "")
        if word in group_settings['bad_words']:
            group_settings['bad_words'].remove(word)
            save_settings()
            bot.answer_callback_query(call.id, f"{word} حذف شد")
        send_admin_panel(chat_id)

    elif call.data == "toggle_links":
        group_settings['lock_links'] = not group_settings['lock_links']
        save_settings()
        status = "روشن" if group_settings['lock_links'] else "خاموش"
        bot.answer_callback_query(call.id, f"قفل لینک {status}")
        send_admin_panel(chat_id)

    elif call.data == "toggle_media":
        group_settings['lock_media'] = not group_settings['lock_media']
        save_settings()
        status = "روشن" if group_settings['lock_media'] else "خاموش"
        bot.answer_callback_query(call.id, f"قفل مدیا {status}")
        send_admin_panel(chat_id)

    elif call.data == "security":
        bot.send_message(chat_id, "⚠ تنظیمات امنیتی:\nحداقل سن اکانت: "
                         f"{group_settings['min_account_days']} روز\nضد اسپم: "
                         f"{group_settings['spam_limit']} پیام/10ثانیه")
        send_admin_panel(chat_id)

    elif call.data == "cleaning":
        bot.send_message(chat_id, f"🧹 پاکسازی:\nJoin/Left: {'✅' if group_settings['clean_join'] else '❌'}\nPin: {'✅' if group_settings['clean_pin'] else '❌'}")
        send_admin_panel(chat_id)

    elif call.data == "help":
        help_text = (
            "📚 راهنمای دستورات:\n"
            "/panel - پنل مدیریت\n"
            "➕ افزودن/حذف کلمات بد\n"
            "🔗 قفل لینک، 🖼 قفل مدیا\n"
            "⚠ امنیت: محدودیت سن اکانت و ضد اسپم\n"
            "🧹 پاکسازی پیام‌های سیستمی\n"
        )
        bot.send_message(chat_id, help_text)
        send_admin_panel(chat_id)

    elif call.data == "exit":
        bot.delete_message(chat_id, call.message.message_id)

def add_bad_word(message):
    chat_id = message.chat.id
    word = message.text.strip()
    ensure_group_settings(chat_id)
    group_settings = settings[str(chat_id)]
    if word not in group_settings['bad_words']:
        group_settings['bad_words'].append(word)
        save_settings()
    bot.send_message(chat_id, f"{word} اضافه شد ✅")
    send_admin_panel(chat_id)

# پاسخ‌های خودکار
auto_responses = {
    'برلین': ["جانم عشقم", "چی شده", "چته", "ها", "بگو", "برو پیویش"],
    'berlin': ["Yes?", "I’m here", "Tell me", "Go ahead"],
    'سپهر': ["جانم عشقم", "ها", "بگو"]
}
response_index = {}

# مدیریت پیام‌ها
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'sticker'])
def handle_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = (message.text or "").lower()
    ensure_group_settings(chat_id)
    group_settings = settings[str(chat_id)]

    # ضد اسپم
    now = time.time()
    user_msgs = spam_tracker.get(user_id, [])
    user_msgs = [t for t in user_msgs if now - t < 10]
    user_msgs.append(now)
    spam_tracker[user_id] = user_msgs
    if len(user_msgs) > group_settings['spam_limit']:
        bot.delete_message(chat_id, message.message_id)
        return

    # کلمات بد
    for bad in group_settings['bad_words']:
        if bad in text:
            bot.delete_message(chat_id, message.message_id)
            bot.send_message(chat_id, "🚫 پیام حاوی کلمه نامناسب حذف شد. لطفا رعایت کنید 🌹")
            return

    # قفل لینک
    if group_settings['lock_links'] and link_pattern.search(text):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "🚫 ارسال لینک ممنوع است")
        return

    # قفل مدیا
    if group_settings['lock_media'] and message.content_type in ['photo', 'video', 'document', 'audio']:
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, "🚫 ارسال مدیا ممنوع است")
        return

    # پاسخ خودکار
    for key, responses in auto_responses.items():
        if key in text:
            idx = response_index.get((chat_id, key), 0)
            bot.send_message(chat_id, responses[idx])
            response_index[(chat_id, key)] = (idx + 1) % len(responses)
            return

print("🤖 Berlin Anti Pro آماده کار است...")
bot.infinity_polling()