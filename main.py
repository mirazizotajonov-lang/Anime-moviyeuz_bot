# =========================================================
# 🔥 ULTRA ANIME BOT UZ
# 👑 FULL PROFESSIONAL VERSION
# =========================================================

TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
MAIN_CHANNEL = "@anime_movieuz"

CHANNELS = [
    "@anime_movieuz",
    "@kanal2",
    "@kanal3",
    "@kanal4",
    "@kanal5",
    "@kanal6",
    "@kanal7",
    "@kanal8",
    "@kanal9",
    "@kanal10"
]

import asyncio
import sqlite3
import os
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import *
from aiogram.enums import ParseMode

# BARQAROR VERSUYA UCHUN ASLIY ULANIY
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

db = sqlite3.connect("anime.db", check_same_thread=False)
sql = db.cursor()
sql.execute("PRAGMA journal_mode=WAL")
sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT, name TEXT, description TEXT, photo TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, episode TEXT, video TEXT)")
db.commit()

app = Flask('')

@app.route('/')
def home():
    return "BOT ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

async def save_user(user_id):
    user = sql.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        sql.execute("INSERT INTO users VALUES(?)", (user_id,))
        db.commit()

async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="➕ Qism qo'shish")],
        [KeyboardButton(text="🗂 Animelar ro'yhati"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Kanal post"), KeyboardButton(text="📨 Broadcast")],
        [KeyboardButton(text="🏧 Admin")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: Message):
    await save_user(message.from_user.id)
    args = message.text.split()
    code_from_link = args[1] if len(args) > 1 else None

    check = await check_sub(message.from_user.id)
    if not check:
        buttons = []
        for ch in CHANNELS:
            buttons.append(
