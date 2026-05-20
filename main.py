# =========================================================
# 🔥 ULTRA ANIME BOT UZ
# 👑 FULL PROFESSIONAL VERSION
# ⚡ FAST | ☁️ 24/7 | 🎬 ANIME SYSTEM | 🔒 FORCE SUB
# =========================================================

# =========================
# CONFIG
# =========================
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
MAIN_CHANNEL = "@anime_movieuz"

# SENING 10 TA KANALING RO'YXATI
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

# =========================
# IMPORTS
# =========================
import asyncio
import sqlite3
import random
import os
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import *
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# =========================
# BOT
# =========================
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# =========================
# DATABASE FAST
# =========================
db = sqlite3.connect("anime.db", check_same_thread=False)
sql = db.cursor()
sql.execute("PRAGMA journal_mode=WAL")

sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT, name TEXT, description TEXT, photo TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, episode TEXT, video TEXT)")
db.commit()

# =========================
# 24/7 WEB SERVER
# =========================
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

# =========================
# SYSTEM FUNCTIONS
# =========================
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
# =========================
# HANDLERS START
# =========================
@dp.message(Command("start"))
async def start(message: Message):
    await save_user(message.from_user.id)
    args = message.text.split()
    code_from_link = args[1] if len(args) > 1 else None

    check = await check_sub(message.from_user.id)
    if not check:
        buttons = []
        for ch in CHANNELS:
            buttons.append([InlineKeyboardButton(text=f"❌ {ch}", url=f"https://t.me/{ch.replace('@','')}")])
        cb_data = f"check_sub_{code_from_link}" if code_from_link else "check_sub"
        buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=cb_data)])
        return await message.answer("🔒 Kanallarga obuna bo'ling!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    if code_from_link:
        await send_anime_by_code(message, code_from_link)
    elif message.from_user.id == ADMIN_ID:
        await message.answer("🎛 Boshqaruv panel", reply_markup=admin_menu)
    else:
        await message.answer("👋 Xush kelibsiz!\n\n🍿 Anime kodini kiriting")

@dp.callback_query(F.data.startswith("check_sub"))
async def checksub(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    code = data_parts[2] if len(data_parts) > 2 else None
    if await check_sub(callback.from_user.id):
        await callback.message.delete()
        if code: await send_anime_by_code(callback.message, code)
        else: await callback.message.answer("✅ Obuna tasdiqlandi\n\n🍿 Anime kodini kiriting")
    else:
        await callback.answer("❌ Hali obuna bo'lmadingiz", show_alert=True)

step = {}
anime_data = {}

@dp.message(F.text == "➕ Anime qo'shish")
async def addanime(message: Message):
    if message.from_user.id == ADMIN_ID:
        step[message.from_user.id] = "code"
        await message.answer("🎬 Anime kodini yuboring:")

@dp.message(F.text == "➕ Qism qo'shish")
async def add_episode_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        step[message.from_user.id] = "ep_code"
        await message.answer("Qaysi anime kodiga qism qo'shmoqchisiz?:")

@dp.message(F.text == "📨 Broadcast")
async def broadcast_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        step[message.from_user.id] = "broadcast"
        await message.answer("Reklama xabarini kiriting:")

@dp.message(F.text == "📢 Kanal post")
async def kanal_post_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        step[message.from_user.id] = "kanal_post"
        await message.answer("Kanalga yuboriladigan postni yuboring:")

@dp.message(F.text == "🏧 Admin")
async def admin_msg(message: Message):
    await message.answer(f"🏧 Admin ID: {ADMIN_ID}")

async def send_anime_by_code(message: Message, code: str):
    anime = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
    if anime:
        btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📺 Tomosha qilish", callback_data=f"watch_{anime[0]}")],
            [InlineKeyboardButton(text="🗑 Animeni o'chirish", callback_data=f"delete_{anime[0]}")]
        ])
        bot_username = (await bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={anime[0]}"
        await bot.send_photo(chat_id=message.chat.id, photo=anime[3], caption=f"🍿 <b>{anime[1]}</b>\n\n🆔 Kodi: <code>{anime[0]}</code>\n\n🎞 {anime[2]}\n\n🔗 Link: {link}", reply_markup=btn)
    else:
        if message.from_user.id != ADMIN_ID:
            await bot.send_message(message.chat.id, "❌ Anime topilmadi")

@dp.message()
async def system(message: Message):
    user = message.from_user.id
    if user in step:
        if step[user] == "broadcast":
            del step[user]
            await message.answer("📢 Yuborilmoqda...")
            for u in sql.execute("SELECT id FROM users").fetchall():
                try: await message.copy_to(chat_id=u[0])
                except: pass
            return await message.answer("✅ Tugadi.")
        if step[user] == "code":
            anime_data[user] = {"code": message.text}
            step[user] = "name"
            return await message.answer("🍿 Anime nomini yuboring:")
        if step[user] == "name":
            anime_data[user]["name"] = message.text
            step[user] = "desc"
            return await message.answer("🎞 Anime tavsifini yuboring:")
        if step[user] == "desc":
            anime_data[user]["desc"] = message.text
            step[user] = "photo"
            return await message.answer("🏞 Anime rasmini yuboring:")
        if step[user] == "photo":
            if not message.photo: return await message.answer("❌ Rasm yuboring")
            sql.execute("INSERT INTO anime VALUES(?,?,?,?)", (anime_data[user]["code"], anime_data[user]["name"], anime_data[user]["desc"], message.photo[-1].file_id))
            db.commit()
            del step[user]
            return await message.answer("✅ Anime saqlandi")
        if step[user] == "ep_code":
            anime_data[user] = {"ep_code": message.text}
            step[user] = "ep_num"
            return await message.answer("Qism raqamini kiriting:")
        if step[user] == "ep_num":
            anime_data[user]["ep_num"] = message.text
            step[user] = "ep_video"
            return await message.answer("🎬 Videoni yuboring:")
        if step[user] == "ep_video":
            if not message.video: return await message.answer("❌ Video yuboring!")
            sql.execute("INSERT INTO episodes VALUES(?,?,?)", (anime_data[user]["ep_code"], anime_data[user]["ep_num"], message.video.file_id))
            db.commit()
            del step[user]
            return await message.answer("✅ Qism qo'shildi!")
    if message.text and not message.text.startswith("/"):
        await send_anime_by_code(message, message.text)

@dp.callback_query(F.data.startswith("watch_"))
async def watch(callback: CallbackQuery):
    code = callback.data.split("_")[1]
    episodes = sql.execute("SELECT * FROM episodes WHERE anime_code=?", (code,)).fetchall()
    if not episodes: return await callback.answer("❌ Qism yo'q", show_alert=True)
    await callback.answer("Yuklanmoqda...")
    for ep in episodes:
        try: await callback.message.answer_video(video=ep[2], caption=f"🎬 {ep[1]}")
        except: pass

@dp.callback_query(F.data.startswith("delete_"))
async def delete_anime_callback(callback: CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        code = callback.data.split("_")[1]
        sql.execute("DELETE FROM anime WHERE code=?", (code,))
        sql.execute("DELETE FROM episodes WHERE anime_code=?", (code,))
        db.commit()
        await callback.message.delete()
        await callback.message.answer("🗑 O'chirildi!")

@dp.message(F.text == "🗂 Animelar ro'yhati")
async def animelist(message: Message):
    animes = sql.execute("SELECT * FROM anime").fetchall()
    if not animes: return await message.answer("Baza bo'sh.")
    text = "🗂 Animelar:\n\n"
    for anime in animes: text += f"🍿 {anime[1]} - {anime[0]}\n"
    await message.answer(text)

@dp.message(F.text == "📊 Statistika")
async def stat(message: Message):
    users = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    anime = sql.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
    await message.answer(f"📊 Obunachilar: {users}\n🍿 Animelar: {anime}")

async def main():
    keep_alive()
    print("BOT ISHLADI")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
