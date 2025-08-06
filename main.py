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
settings = {}
spam_tracker = {}
warnings = {}

default_settings = {
    'bad_words': ['سیک', 'کیر', 'کص', 'حرومزاده'],
    'lock_links': True,
    'lock_media': False,
    'lock_sticker': False,
    'lock_gif': False,
    'lock_forward': True,
    'min_account_days': 0,
    'spam_limit': 5,
    'clean_join': True,
    'clean_pin': True,
    'welcome_enabled': True,
    'welcome_text': "🌸 خوش آمدی {name} به گروه {chat}!\nلطفا قوانین را رعایت کن.",
    'welcome_button': "📜 قوانین گروه"
}

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

link_pattern = re.compile(r'(http|https|t\.me|telegram\.me|www\.|\.com)')

# ---------------- پنل ----------------
def update_panel(chat_id, message_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📝 کلمات بد", callback_data="badwords"),
        types.InlineKeyboardButton("🔗 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("⚠ امنیت", callback_data="security"),
        types.InlineKeyboardButton("🎉 خوش‌آمدگویی", callback_data="welcome"),
        types.InlineKeyboardButton("📚 راهنما", callback_data="help"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close")
    )
    bot.edit_message_text("🔧 پنل مدیریت Berlin Anti Ultra++", chat_id, message_id, reply_markup=kb)

@bot.message_handler(commands=['panel'])
def panel_cmd(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "🚫 فقط ادمین‌ها اجازه دارند.")
        return
    ensure_group_settings(message.chat.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📂 باز کردن پنل", callback_data="openpanel"))
    bot.send_message(message.chat.id, "🔧 برای مدیریت گروه روی دکمه زیر کلیک کنید:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    ensure_group_settings(chat_id)
    group_settings = settings[str(chat_id)]

    if call.data == "openpanel":
        update_panel(chat_id, msg_id)

    elif call.data == "badwords":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ افزودن", callback_data="addbad"),
               types.InlineKeyboardButton("➖ حذف", callback_data="removebad"),
               types.InlineKeyboardButton("🔙 برگشت", callback_data="openpanel"))
        words = "\n".join(group_settings['bad_words'])
        bot.edit_message_text(f"📝 کلمات بد:\n{words}", chat_id, msg_id, reply_markup=kb)

    elif call.data == "addbad":
        msg = bot.send_message(chat_id, "🔤 کلمه بد جدید را ارسال کنید:")
        bot.register_next_step_handler(msg, lambda m: add_bad(m, msg_id))

    elif call.data == "removebad":
        kb = types.InlineKeyboardMarkup()
        for w in group_settings['bad_words']:
            kb.add(types.InlineKeyboardButton(w, callback_data=f"del_{w}"))
        kb.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="badwords"))
        bot.edit_message_text("❌ انتخاب کلمه برای حذف:", chat_id, msg_id, reply_markup=kb)

    elif call.data.startswith("del_"):
        word = call.data.replace("del_", "")
        if word in group_settings['bad_words']:
            group_settings['bad_words'].remove(word)
            save_settings()
        bot.answer_callback_query(call.id, f"{word} حذف شد")
        update_panel(chat_id, msg_id)

    elif call.data == "locks":
        locks_text = (f"🔗 قفل لینک: {'✅' if group_settings['lock_links'] else '❌'}\n"
                      f"🖼 قفل مدیا: {'✅' if group_settings['lock_media'] else '❌'}\n"
                      f"📎 قفل فوروارد: {'✅' if group_settings['lock_forward'] else '❌'}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔄 تغییر لینک", callback_data="toggle_links"),
               types.InlineKeyboardButton("🔄 تغییر مدیا", callback_data="toggle_media"),
               types.InlineKeyboardButton("🔄 تغییر فوروارد", callback_data="toggle_forward"),
               types.InlineKeyboardButton("🔙 برگشت", callback_data="openpanel"))
        bot.edit_message_text(locks_text, chat_id, msg_id, reply_markup=kb)

    elif call.data.startswith("toggle_"):
        lock_name = call.data.replace("toggle_", "lock_")
        group_settings[lock_name] = not group_settings[lock_name]
        save_settings()
        bot.answer_callback_query(call.id, "✅ تغییر انجام شد")
        update_panel(chat_id, msg_id)

    elif call.data == "security":
        sec_text = f"⚠ حداقل سن اکانت: {group_settings['min_account_days']} روز\n🛡 ضد اسپم: {group_settings['spam_limit']} پیام/10ث"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="openpanel"))
        bot.edit_message_text(sec_text, chat_id, msg_id, reply_markup=kb)

    elif call.data == "welcome":
        wel_text = f"🎉 خوش‌آمدگویی: {'✅' if group_settings['welcome_enabled'] else '❌'}\n\n{group_settings['welcome_text']}"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔄 تغییر متن", callback_data="change_welcome"),
               types.InlineKeyboardButton("🔄 تغییر وضعیت", callback_data="toggle_welcome"),
               types.InlineKeyboardButton("🔙 برگشت", callback_data="openpanel"))
        bot.edit_message_text(wel_text, chat_id, msg_id, reply_markup=kb)

    elif call.data == "toggle_welcome":
        group_settings['welcome_enabled'] = not group_settings['welcome_enabled']
        save_settings()
        bot.answer_callback_query(call.id, "✅ تغییر انجام شد")
        update_panel(chat_id, msg_id)

    elif call.data == "help":
        help_text = (
            "📚 راهنمای Berlin Anti Ultra++:\n\n"
            "دستورات ریپلای:\n"
            "🔹 بن → اخراج کاربر\n"
            "🔹 سکوت / میوت → میوت کاربر\n"
            "🔹 آزاد / آن‌میوت → آزاد کردن کاربر\n\n"
            "دستورات پنل:\n"
            "🔹 /panel → باز کردن پنل\n"
            "🔹 افزودن / حذف کلمات بد\n"
            "🔹 قفل‌ها: لینک، مدیا، فوروارد\n"
            "🔹 خوش‌آمدگویی سفارشی\n"
            "🔹 امنیت: ضد اسپم، حداقل سن"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="openpanel"))
        bot.edit_message_text(help_text, chat_id, msg_id, reply_markup=kb)

    elif call.data == "close":
        bot.delete_message(chat_id, msg_id)

def add_bad(message, panel_id):
    chat_id = message.chat.id
    word = message.text.strip()
    group_settings = settings[str(chat_id)]
    if word not in group_settings['bad_words']:
        group_settings['bad_words'].append(word)
        save_settings()
    bot.send_message(chat_id, f"✅ کلمه {word} اضافه شد")
    update_panel(chat_id, panel_id)

# ---------------- ریپلای دستورات ----------------
@bot.message_handler(func=lambda m: m.reply_to_message and m.text)
def reply_commands(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not is_admin(chat_id, user_id):
        return

    cmd = message.text.strip().lower()
    target_id = message.reply_to_message.from_user.id

    if "بن" in cmd:
        bot.kick_chat_member(chat_id, target_id)
        bot.reply_to(message, "🚫 کاربر بن شد.")

    elif "سکوت" in cmd or "میوت" in cmd:
        bot.restrict_chat_member(chat_id, target_id, can_send_messages=False)
        bot.reply_to(message, "🔇 کاربر سکوت شد.")

    elif "آزاد" in cmd or "آن‌میوت" in cmd:
        bot.restrict_chat_member(chat_id, target_id,
                                 can_send_messages=True,
                                 can_send_media_messages=True,
                                 can_send_other_messages=True,
                                 can_add_web_page_previews=True)
        bot.reply_to(message, "🔊 سکوت کاربر برداشته شد.")

# ---------------- فیلتر پیام‌ها ----------------
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'sticker'])
def filter_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = (message.text or "").lower()
    ensure_group_settings(chat_id)
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

    # کلمات بد
    for bad in group_settings['bad_words']:
        if bad in text:
            bot.delete_message(chat_id, message.message_id)
            return

    # قفل لینک
    if group_settings['lock_links'] and link_pattern.search(text):
        bot.delete_message(chat_id, message.message_id)
        return

    # قفل مدیا
    if group_settings['lock_media'] and message.content_type in ['photo', 'video', 'document', 'audio']:
        bot.delete_message(chat_id, message.message_id)
        return

    # قفل فوروارد
    if group_settings['lock_forward'] and message.forward_from:
        bot.delete_message(chat_id, message.message_id)
        return

print("🔥 Berlin Anti Ultra++ فعال شد...")
bot.infinity_polling()