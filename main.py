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

# USERS
sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
# ANIME
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT, name TEXT, description TEXT, photo TEXT)")
# EPISODES
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, episode TEXT, video TEXT)")
db.commit()

# =========================
# 24/7 WEB SERVER (RENDER PORTI UCHUN)
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
# SAVE USER
# =========================
async def save_user(user_id):
    user = sql.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        sql.execute("INSERT INTO users VALUES(?)", (user_id,))
        db.commit()

# =========================
# FORCE SUB
# =========================
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# =========================
# MENU
# =========================
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
# START
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
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        return await message.answer("🔒 Kanallarga obuna bo'ling!", reply_markup=kb)

    if code_from_link:
        await send_anime_by_code(message, code_from_link)
    elif message.from_user.id == ADMIN_ID:
        await message.answer("🎛 Boshqaruv panel", reply_markup=admin_menu)
    else:
        await message.answer("👋 Xush kelibsiz!\n\n🍿 Anime kodini kiriting\n🔎 Anime qidiring\n📺 Anime tomosha qiling")

# =========================
# CHECK SUB
# =========================
@dp.callback_query(F.data.startswith("check_sub"))
async def checksub(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    code = data_parts[2] if len(data_parts) > 2 else None

    check = await check_sub(callback.from_user.id)
    if check:
        await callback.message.delete()
        if code:
            await send_anime_by_code(callback.message, code)
        else:
            await callback.message.answer("✅ Obuna tasdiqlandi\n\n🍿 Anime kodini kiriting")
    else:
        await callback.answer("❌ Hali obuna bo'lmadingiz", show_alert=True)

# =========================
# ADD ANIME & STEPS
# =========================
step = {}
anime_data = {}

@dp.message(F.text == "➕ Anime qo'shish")
async def addanime(message: Message):
    if message.from_user.id != ADMIN_ID: return
    step[message.from_user.id] = "code"
    await message.answer("🎬 Anime kodini yuboring:")

@dp.message(F.text == "➕ Qism qo'shish")
async def add_episode_start(message: Message):
    if message.from_user.id != ADMIN_ID: return
    step[message.from_user.id] = "ep_code"
    await message.answer("Qaysi anime kodiga qism qo'shmoqchisiz? Kodni kiriting:")

@dp.message(F.text == "📨 Broadcast")
async def broadcast_start(message: Message):
    if message.from_user.id != ADMIN_ID: return
    step[message.from_user.id] = "broadcast"
    await message.answer("Barcha a'zolarga yuboriladigan xabarni (reklamani) kiriting:")

@dp.message(F.text == "📢 Kanal post")
async def kanal_post_start(message: Message):
    if message.from_user.id != ADMIN_ID: return
    step[message.from_user.id] = "kanal_post"
    await message.answer("Asosiy kanalga yuboriladigan post matni yoki rasmini yuboring:")

@dp.message(F.text == "🏧 Admin")
async def admin_msg(message: Message):
    await message.answer(f"🏧 Savollar yoki takliflar bo'lsa, Adminga murojaat qiling: tg://user?id={ADMIN_ID}")

async def send_anime_by_code(message: Message, code: str):
    anime = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
    if anime:
        btn = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📺 Tomosha qilish", callback_data=f"watch_{anime[0]}")],
                [InlineKeyboardButton(text="✏ Nomni o'zgartirish", callback_data=f"editname_{anime[0]}")],
                [InlineKeyboardButton(text="🏞 Rasmni o'zgartirish", callback_data=f"editphoto_{anime[0]}")],
                [InlineKeyboardButton(text="🎞 Tavsifni o'zgartirish", callback_data=f"editdesc_{anime[0]}")],
                [InlineKeyboardButton(text="🗑 Animeni o'chirish", callback_data=f"delete_{anime[0]}")]
            ]
        )
        bot_username = (await bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={anime[0]}"

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=anime[3],
            caption=f"🍿 <b>{anime[1]}</b>\n\n🆔 Kodi: <code>{anime[0]}</code>\n\n🎞 {anime[2]}\n\n🔗 Kanal uchun link: <code>{link}</code>",
            reply_markup=btn
        )
    else:
        if message.from_user.id != ADMIN_ID or (message.text and not message.text.startswith("/")):
            await bot.send_message(message.chat.id, "❌ Anime topilmadi boshqa kod kiriting")

# =========================
# STEP SYSTEM PROCESSING
# =========================
@dp.message()
async def system(message: Message):
    user = message.from_user.id

    if user in step:
        if step[user] == "broadcast":
            del step[user]
            await message.answer("📢 Reklama yuborilmoqda...")
            all_users = sql.execute("SELECT id FROM users").fetchall()
            count = 0
            for u in all_users:
                try:
                    await message.copy_to(chat_id=u[0])
                    count += 1
                except: pass
            return await message.answer(f"✅ Reklama {count} ta foydalanuvchiga yuborildi.")

        if step[user] == "kanal_post":
            del step[user]
            try:
                await message.copy_to(chat_id=CHANNELS[0])
                return await message.answer("✅ Post asosiy kanalga yuborildi!")
            except Exception as e:
                return await message.answer(f"❌ Kanalga yuborishda xatolik: {e}")

        if step[user] == "code":
            anime_data[user] = {}
            anime_data[user]["code"] = message.text
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
            if not message.photo:
                return await message.answer("❌ Rasm yuboring")
            anime_data[user]["photo"] = message.photo[-1].file_id
            sql.execute("INSERT INTO anime VALUES(?,?,?,?)", (anime_data[user]["code"], anime_data[user]["name"], anime_data[user]["desc"], anime_data[user]["photo"]))
            db.commit()
            del step[user]
            return await message.answer("✅ Anime saqlandi")

        if step[user] == "ep_code":
            anime_data[user] = {"ep_code": message.text}
            step[user] = "ep_num"
            return await message.answer("Qism nomini yoki tartib raqamini kiriting (Masalan: 1-qism):")

        if
