import os
import telebot
from telebot import types
import json
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

settings_file = 'settings.json'
settings = {}
spam_tracker = {}
warns = {}

default_settings = {
    'bad_words': ['کص', 'سیک', 'کیر', 'حرومزاده'],  # 👈 کلمات پیش‌فرض
    'spam_limit': 5,
    'welcome': True,
    'welcome_text': "🌸 خوش آمدی {name} به گروه {chat}!",
}

# ---------- ذخیره و لود تنظیمات ----------
def load_settings():
    global settings
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except:
        settings = {}

def save_settings():
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

load_settings()

def ensure_group(chat_id):
    if str(chat_id) not in settings:
        settings[str(chat_id)] = default_settings.copy()
        save_settings()

def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

# ---------- پنل ----------
@bot.message_handler(commands=['panel'])
def panel(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "🚫 فقط ادمین‌ها دسترسی دارند.")
        return
    ensure_group(message.chat.id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 مدیریت کاربران", callback_data="users"),
        types.InlineKeyboardButton("📜 فیلتر کلمات", callback_data="badwords"),
        types.InlineKeyboardButton("⚠ ضد اسپم", callback_data="spam"),
        types.InlineKeyboardButton("🎉 خوش‌آمد", callback_data="welcome"),
        types.InlineKeyboardButton("ℹ راهنما", callback_data="help")
    )
    bot.send_message(message.chat.id, "🔧 پنل مدیریت Berlin Anti", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    ensure_group(chat_id)
    group_settings = settings[str(chat_id)]

    if call.data == "users":
        bot.edit_message_text("👤 مدیریت کاربران:\nMute / Unmute / Ban / Unban / Warn / Clearwarn",
                              chat_id, call.message.message_id)

    elif call.data == "badwords":
        words = "\n".join(group_settings['bad_words']) or "کلمه‌ای ثبت نشده."
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ افزودن", callback_data="addbad"),
               types.InlineKeyboardButton("➖ حذف", callback_data="removebad"))
        bot.edit_message_text(f"📜 لیست کلمات:\n{words}", chat_id, call.message.message_id, reply_markup=kb)

    elif call.data == "addbad":
        msg = bot.send_message(chat_id, "کلمه بد جدید رو بفرست:")
        bot.register_next_step_handler(msg, lambda m: add_bad(m))

    elif call.data == "removebad":
        if not group_settings['bad_words']:
            bot.answer_callback_query(call.id, "❌ لیست خالیه")
        else:
            kb = types.InlineKeyboardMarkup()
            for w in group_settings['bad_words']:
                kb.add(types.InlineKeyboardButton(w, callback_data=f"del_{w}"))
            bot.edit_message_text("❌ انتخاب کلمه برای حذف:", chat_id, call.message.message_id, reply_markup=kb)

    elif call.data.startswith("del_"):
        w = call.data.replace("del_", "")
        if w in group_settings['bad_words']:
            group_settings['bad_words'].remove(w)
            save_settings()
            bot.answer_callback_query(call.id, f"{w} حذف شد")

    elif call.data == "spam":
        bot.edit_message_text(f"⚠ ضد اسپم فعال. محدودیت: {group_settings['spam_limit']} پیام/10ث",
                              chat_id, call.message.message_id)

    elif call.data == "welcome":
        status = "✅ فعال" if group_settings['welcome'] else "❌ غیرفعال"
        bot.edit_message_text(f"🎉 خوش‌آمدگویی: {status}\nمتن: {group_settings['welcome_text']}",
                              chat_id, call.message.message_id)

    elif call.data == "help":
        help_text = (
            "ℹ راهنما:\n"
            "- بن: با ریپلای روی کاربر «بن» بزن\n"
            "- سکوت: با ریپلای «سکوت» یا «میوت» بزن\n"
            "- آزاد: با ریپلای «آزاد» بزن\n"
            "- اخطار: با ریپلای «اخطار» بزن\n"
            "- پاک اخطار: با ریپلای «پاک اخطار» بزن\n"
            "- فیلتر کلمات از پنل\n"
        )
        bot.edit_message_text(help_text, chat_id, call.message.message_id)

def add_bad(message):
    chat_id = message.chat.id
    word = message.text.strip()
    group_settings = settings[str(chat_id)]
    group_settings['bad_words'].append(word)
    save_settings()
    bot.reply_to(message, f"✅ {word} اضافه شد")

# ---------- دستورات بدون / ----------
@bot.message_handler(func=lambda m: m.reply_to_message and m.text)
def reply_cmd(message):
    chat_id = message.chat.id
    if not is_admin(chat_id, message.from_user.id):
        return

    cmd = message.text.lower()
    target_id = message.reply_to_message.from_user.id

    if "بن" in cmd:
        bot.kick_chat_member(chat_id, target_id)
        bot.reply_to(message, "🚫 کاربر بن شد")

    elif "سکوت" in cmd or "میوت" in cmd:
        bot.restrict_chat_member(chat_id, target_id, can_send_messages=False)
        bot.reply_to(message, "🔇 کاربر میوت شد")

    elif "آزاد" in cmd:
        bot.restrict_chat_member(chat_id, target_id, can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=True)
        bot.reply_to(message, "🔊 کاربر آزاد شد")

    elif "اخطار" in cmd:
        warns[target_id] = warns.get(target_id, 0) + 1
        bot.reply_to(message, f"⚠ اخطار {warns[target_id]} داده شد")

    elif "پاک اخطار" in cmd:
        warns[target_id] = 0
        bot.reply_to(message, "✅ اخطارها پاک شد")

# ---------- فیلتر کلمات + ضد اسپم ----------
@bot.message_handler(func=lambda m: True, content_types=['text'])
def filter_msg(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()
    ensure_group(chat_id)
    group_settings = settings[str(chat_id)]

    # ضد اسپم
    now = time.time()
    msgs = spam_tracker.get(user_id, [])
    msgs = [t for t in msgs if now - t < 10]
    msgs.append(now)
    spam_tracker[user_id] = msgs
    if len(msgs) > group_settings['spam_limit']:
        bot.delete_message(chat_id, message.message_id)
        return

    # ضد فحش
    for bad in group_settings['bad_words']:
        if bad in text:
            bot.delete_message(chat_id, message.message_id)
            bot.send_message(chat_id, "🚫 لطفا ادب رو رعایت کنید")
            return

# ---------- خوش آمدگویی ----------
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    chat_id = message.chat.id
    ensure_group(chat_id)
    group_settings = settings[str(chat_id)]
    if group_settings['welcome']:
        for m in message.new_chat_members:
            bot.send_message(chat_id, group_settings['welcome_text'].format(
                name=m.first_name, chat=message.chat.title))

print("🚀 Berlin Anti فعال شد")
bot.infinity_polling()