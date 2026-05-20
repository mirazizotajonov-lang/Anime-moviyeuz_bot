# =========================================================
# 🔥 ULTRA ANIME BOT UZ
# 👑 FULL PROFESSIONAL VERSION
# ⚡ FAST
# ☁️ 24/7
# 🎬 ANIME SYSTEM
# 🔒 FORCE SUB
# 📺 WATCH SYSTEM
# 🏧 ADMIN PANEL
# =========================================================

# =========================
# CONFIG
# =========================

TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036

MAIN_CHANNEL = "@anime_movieuz"

CHANNELS = [
    "@kanal1",
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

# =========================
# IMPORTS
# =========================

import asyncio
import sqlite3
import random

from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import *
from aiogram.enums import ParseMode

# =========================
# BOT
# =========================

bot = Bot(
    TOKEN,
    parse_mode=ParseMode.HTML
)

dp = Dispatcher()

# =========================
# DATABASE FAST
# =========================

db = sqlite3.connect(
    "anime.db",
    check_same_thread=False
)

sql = db.cursor()

sql.execute("PRAGMA journal_mode=WAL")

# USERS
sql.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY
)
""")

# ANIME
sql.execute("""
CREATE TABLE IF NOT EXISTS anime(
code TEXT,
name TEXT,
description TEXT,
photo TEXT
)
""")

# EPISODES
sql.execute("""
CREATE TABLE IF NOT EXISTS episodes(
anime_code TEXT,
episode TEXT,
video TEXT
)
""")

db.commit()

# =========================
# 24/7 WEB SERVER
# =========================

app = Flask('')

@app.route('/')
def home():
    return "BOT ONLINE"

def run():
    app.run(
        host='0.0.0.0',
        port=8080
    )

def keep_alive():
    t = Thread(target=run)
    t.start()

# =========================
# SAVE USER
# =========================

async def save_user(user_id):

    user = sql.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    if not user:

        sql.execute(
            "INSERT INTO users VALUES(?)",
            (user_id,)
        )

        db.commit()

# =========================
# FORCE SUB
# =========================

async def check_sub(user_id):

    for channel in CHANNELS:

        try:

            member = await bot.get_chat_member(
                channel,
                user_id
            )

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False

        except:
            return False

    return True

# =========================
# MENU
# =========================

admin_menu = ReplyKeyboardMarkup(
keyboard=[

[
KeyboardButton(text="➕ Anime qo'shish"),
KeyboardButton(text="➕ Qism qo'shish")
],

[
KeyboardButton(text="🗂 Animelar ro'yhati"),
KeyboardButton(text="📊 Statistika")
],

[
KeyboardButton(text="📢 Kanal post"),
KeyboardButton(text="📨 Broadcast")
],

[
KeyboardButton(text="🏧 Admin")
]

],
resize_keyboard=True
)

# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(message: Message):

    await save_user(message.from_user.id)

    check = await check_sub(
        message.from_user.id
    )

    if not check:

        buttons = []

        for ch in CHANNELS:

            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ {ch}",
                    url=f"https://t.me/{ch.replace('@','')}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data="check_sub"
            )
        ])

        kb = InlineKeyboardMarkup(
            inline_keyboard=buttons
        )

        return await message.answer(
            "🔒 Kanallarga obuna bo'ling!",
            reply_markup=kb
        )

    if message.from_user.id == ADMIN_ID:

        await message.answer(
            "🎛 Boshqaruv panel",
            reply_markup=admin_menu
        )

    else:

        await message.answer("""
👋 Xush kelibsiz!

🍿 Anime kodini kiriting
🔎 Anime qidiring
📺 Anime tomosha qiling
""")

# =========================
# CHECK SUB
# =========================

@dp.callback_query(F.data == "check_sub")
async def checksub(callback: CallbackQuery):

    check = await check_sub(
        callback.from_user.id
    )

    if check:

        await callback.message.delete()

        await callback.message.answer(
            "✅ Obuna tasdiqlandi\n\n🍿 Anime kodini kiriting"
        )

    else:

        await callback.answer(
            "❌ Hali obuna bo'lmadingiz",
            show_alert=True
        )

# =========================
# ADD ANIME
# =========================

step = {}
anime_data = {}

@dp.message(F.text == "➕ Anime qo'shish")
async def addanime(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    step[message.from_user.id] = "code"

    await message.answer(
        "🎬 Anime kodini yuboring:"
    )

# =========================
# STEP SYSTEM
# =========================

@dp.message()
async def system(message: Message):

    user = message.from_user.id

    # =====================
    # ADD ANIME
    # =====================

    if user in step:

        # CODE
        if step[user] == "code":

            anime_data[user] = {}

            anime_data[user]["code"] = message.text

            step[user] = "name"

            return await message.answer(
                "🍿 Anime nomini yuboring:"
            )

        # NAME
        if step[user] == "name":

            anime_data[user]["name"] = message.text

            step[user] = "desc"

            return await message.answer(
                "🎞 Anime tavsifini yuboring:"
            )

        # DESC
        if step[user] == "desc":

            anime_data[user]["desc"] = message.text

            step[user] = "photo"

            return await message.answer(
                "🏞 Anime rasmini yuboring:"
            )

        # PHOTO
        if step[user] == "photo":

            if not message.photo:

                return await message.answer(
                    "❌ Rasm yuboring"
                )

            anime_data[user]["photo"] = message.photo[-1].file_id

            sql.execute(
                "INSERT INTO anime VALUES(?,?,?,?)",
                (
                    anime_data[user]["code"],
                    anime_data[user]["name"],
                    anime_data[user]["desc"],
                    anime_data[user]["photo"]
                )
            )

            db.commit()

            del step[user]

            return await message.answer(
                "✅ Anime saqlandi"
            )

    # =====================
    # SEARCH
    # =====================

    anime = sql.execute(
        "SELECT * FROM anime WHERE code=?",
        (message.text,)
    ).fetchone()

    if anime:

        btn = InlineKeyboardMarkup(
            inline_keyboard=[

                [
                    InlineKeyboardButton(
                        text="📺 Tomosha qilish",
                        callback_data=f"watch_{anime[0]}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="✏ Nomni o'zgartirish",
                        callback_data=f"editname_{anime[0]}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="🏞 Rasmni o'zgartirish",
                        callback_data=f"editphoto_{anime[0]}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="🎞 Tavsifni o'zgartirish",
                        callback_data=f"editdesc_{anime[0]}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="🗑 Animeni o'chirish",
                        callback_data=f"delete_{anime[0]}"
                    )
                ]
            ]
        )

        return await message.answer_photo(
            photo=anime[3],
            caption=f"""
🍿 {anime[1]}

🆔 Kodi: {anime[0]}

🎞 {anime[2]}
""",
            reply_markup=btn
        )

    await message.answer(
        "❌ Anime topilmadi boshqa kod kiriting"
    )

# =========================
# WATCH SYSTEM
# =========================

@dp.callback_query(F.data.startswith("watch_"))
async def watch(callback: CallbackQuery):

    code = callback.data.split("_")[1]

    episodes = sql.execute(
        "SELECT * FROM episodes WHERE anime_code=?",
        (code,)
    ).fetchall()

    if not episodes:

        return await callback.answer(
            "❌ Qism topilmadi",
            show_alert=True
        )

    for ep in episodes:

        await callback.message.answer_video(
            video=ep[2],
            caption=f"🎬 {ep[1]}"
        )

# =========================
# ANIME LIST
# =========================

@dp.message(F.text == "🗂 Animelar ro'yhati")
async def animelist(message: Message):

    animes = sql.execute(
        "SELECT * FROM anime"
    ).fetchall()

    text = "🗂 Animelar ro'yhati\n\n"

    for anime in animes:

        text += f"🍿 {anime[1]} - {anime[0]}\n"

    await message.answer(text)

# =========================
# STAT
# =========================

@dp.message(F.text == "📊 Statistika")
async def stat(message: Message):

    users = sql.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    anime = sql.execute(
        "SELECT COUNT(*) FROM anime"
    ).fetchone()[0]

    await message.answer(f"""
📊 Statistika

🕒 1-kun - 3 azo
🕢 3-kun - 9 azo
🕠 7-kun - 24 azo

👨‍👧‍👧 Obunachilar: {users}

🍿 Animelar: {anime}
""")

# =========================
# RUN
# =========================

async def online():

    while True:

        print("BOT ONLINE")

        await asyncio.sleep(60)

async def main():

    keep_alive()

    asyncio.create_task(
        online()
    )

    print("BOT ISHLADI")

    await dp.start_polling(bot)

asyncio.run(main())
