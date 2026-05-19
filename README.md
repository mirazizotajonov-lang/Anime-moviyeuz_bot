import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread

# Sozlamalar
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
CHANNEL = "@anime_movieuz"

bot = telebot.TeleBot(TOKEN)

# Baza
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS anime (code TEXT PRIMARY KEY, name TEXT, desc TEXT, photo TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
db.commit()

# Majburiy obuna tekshirish
def is_sub(uid):
    try: return bot.get_chat_member(CHANNEL, uid).status in ['member', 'creator', 'administrator']
    except: return False

# Menu
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🔎 Anime qidirish", "🗂 Animelar ro'yxati")
    m.add("📊 Statistika", "⚙️ Admin panel")
    return m

@bot.message_handler(commands=['start'])
def start(m):
    if not is_sub(m.chat.id):
        b = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Obuna bo'lish ➕", url=f"https://t.me/{CHANNEL[1:]}"))
        bot.send_message(m.chat.id, "Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=b)
    else:
        cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (m.chat.id,))
        db.commit()
        bot.send_message(m.chat.id, "Xush kelibsiz! Anime tanlang.", reply_markup=menu())

@bot.message_handler(func=lambda m: m.text == "🔎 Anime qidirish")
def qidirish(m):
    if is_sub(m.chat.id):
        msg = bot.send_message(m.chat.id, "Animening kodini kiritng:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(m.chat.id, "Anime topilmadi yoki xato kod."))

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin panel" and m.from_user.id == ADMIN_ID)
def admin(m):
    bot.send_message(m.chat.id, "Admin paneliga xush kelibsiz!")

# 24/7 ishlash uchun Flask
app = Flask('')
@app.route('/')
def home(): return "Bot ishlayapti!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.infinity_polling()
