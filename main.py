import asyncio
import sqlite3
import os
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import *
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# =========================
# ⚙️ SOZLAMALAR (TOKEN VA ADMIN)
# =========================
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036

# KANALLAR RO'YXATI (OBUNA UCHUN)
CHANNELS = [
    "@anime_movieuz", # Asosiy kanal
    "@kanal2",        # Bularni o'zingni kanalingga almashtir
    "@kanal3",
    "@kanal4",
    "@kanal5"
]

# =========================
# 🤖 BOT VA BAZA INIZIALIZATSIYASI
# =========================
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

db = sqlite3.connect("anime_pro.db", check_same_thread=False)
sql = db.cursor()
sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT PRIMARY KEY, name TEXT, desc TEXT, photo TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, ep_num TEXT, video TEXT)")
db.commit()

# =========================
# 🌐 24/7 ISHLASH UCHUN SERVER (RENDER UCHUN)
# =========================
app = Flask('')
@app.route('/')
def home(): return "BOT ISHLAYAPTI!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# =========================
# 🛠 YORDAMCHI FUNKSIYALAR
# =========================
async def check_sub(user_id):
    if user_id == ADMIN_ID: return True # Admin obuna bo'lishi shart emas
    for ch in CHANNELS:
        try:
            res = await bot.get_chat_member(ch, user_id)
            if res.status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="➕ Qism qo'shish")],
        [KeyboardButton(text="🗂 Animelar ro'yhati"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📨 Broadcast"), KeyboardButton(text="📢 Kanal post")]
    ], resize_keyboard=True
)

# =========================
# 🎬 ASOSIY HANDLERLAR
# =========================
@dp.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    # Foydalanuvchini bazaga qo'shish
    sql.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    db.commit()

    # 👑 ADMIN TEKSHIRUVI (BIRINCHI)
    if user_id == ADMIN_ID:
        return await message.answer("👋 Xush kelibsiz, Admin!\nBoshqaruv paneli tayyor:", reply_markup=admin_menu)

    # 🔒 OBUNA TEKSHIRUVI
    args = message.text.split()
    code = args[1] if len(args) > 1 else None
    
    if not await check_sub(user_id):
        btns = []
        for ch in CHANNELS:
            btns.append([InlineKeyboardButton(text=f"➕ Obuna bo'lish", url=f"https://t.me/{ch.replace('@','')}")])
        cb_data = f"sub_check_{code}" if code else "sub_check_none"
        btns.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=cb_data)])
        return await message.answer("❌ Botdan foydalanish uchun kanallarga obuna bo'ling!", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

    if code:
        await send_anime(message, code)
    else:
        await message.answer("👋 Xush kelibsiz!\nAnime kodini yuboring:")

@dp.callback_query(F.data.startswith("sub_check_"))
async def sub_check_callback(call: CallbackQuery):
    code = call.data.replace("sub_check_", "")
    if await check_sub(call.from_user.id):
        await call.message.delete()
        if code != "none":
            await send_anime(call.message, code)
        else:
            await call.message.answer("✅ Obuna tasdiqlandi! Anime kodini yuboring:")
    else:
        await call.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)

async def send_anime(message: Message, code: str):
    data = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
    if data:
        btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📺 Tomosha qilish", callback_data=f"watch_{code}")],
            [InlineKeyboardButton(text="🗑 O'chirish (Admin)", callback_data=f"del_{code}")]
        ])
        await bot.send_photo(message.chat.id, photo=data[3], caption=f"🍿 <b>{data[1]}</b>\n\n🆔 Kod: <code>{data[0]}</code>\n\n🎞 {data[2]}", reply_markup=btn)
    else:
        await bot.send_message(message.chat.id, "❌ Bunday kodli anime topilmadi!")

# =========================
# 🏗 ADMIN BOSHQARUVI (QADAMMA-QADAM)
# =========================
step = {}
tmp = {}

@dp.message(F.text == "➕ Anime qo'shish")
async def add_1(m: Message):
    if m.from_user.id != ADMIN_ID: return
    step[m.from_user.id] = "get_code"
    await m.answer("1. Anime uchun yangi kod yuboring (Masalan: 101):")

@dp.message()
async def process_steps(m: Message):
    uid = m.from_user.id
    if uid not in step:
        if m.text and not m.text.startswith("/"): await send_anime(m, m.text)
        return

    # ANIME QO'SHISH
    if step[uid] == "get_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "get_name"; await m.answer("2. Anime nomini yuboring:")
    elif step[uid] == "get_name":
        tmp[uid]["name"] = m.text
        step[uid] = "get_desc"; await m.answer("3. Anime tavsifini yuboring:")
    elif step[uid] == "get_desc":
        tmp[uid]["desc"] = m.text
        step[uid] = "get_photo"; await m.answer("4. Anime uchun rasm yuboring:")
    elif step[uid] == "get_photo":
        if not m.photo: return await m.answer("Rasm yuboring!")
        sql.execute("INSERT INTO anime VALUES(?,?,?,?)", (tmp[uid]["code"], tmp[uid]["name"], tmp[uid]["desc"], m.photo[-1].file_id))
        db.commit(); del step[uid]; await m.answer("✅ Anime bazaga qo'shildi!")

    # QISM QO'SHISH
    elif step[uid] == "get_ep_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "get_ep_num"; await m.answer("Qism raqamini yuboring (Masalan: 1-qism):")
    elif step[uid] == "get_ep_num":
        tmp[uid]["num"] = m.text
        step[uid] = "get_ep_vid"; await m.answer("🎬 Videoni yuboring:")
    elif step[uid] == "get_ep_vid":
        if not m.video: return await m.answer("Video yuboring!")
        sql.execute("INSERT INTO episodes VALUES(?,?,?)", (tmp[uid]["code"], tmp[uid]["num"], m.video.file_id))
        db.commit(); del step[uid]; await m.answer("✅ Qism qo'shildi!")

    # BROADCAST
    elif step[uid] == "get_reklama":
        users = sql.execute("SELECT id FROM users").fetchall()
        for u in users:
            try: await m.copy_to(u[0])
            except: pass
        del step[uid]; await m.answer("✅ Reklama tarqatildi!")

@dp.message(F.text == "➕ Qism qo'shish")
async def add_ep_1(m: Message):
    if m.from_user.id == ADMIN_ID:
        step[m.from_user.id] = "get_ep_code"; await m.answer("Qaysi anime kodiga qism qo'shmoqchisiz?")

@dp.message(F.text == "📨 Broadcast")
async def bc_1(m: Message):
    if m.from_user.id == ADMIN_ID:
        step[m.from_user.id] = "get_reklama"; await m.answer("Reklama postini yuboring (Rasm, matn yoki video):")

@dp.message(F.text == "📊 Statistika")
async def stats(m: Message):
    u = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    a = sql.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
    await m.answer(f"📊 <b>Bot statistikasi:</b>\n\n👤 Foydalanuvchilar: {u}\n🍿 Animelar: {a}")

@dp.callback_query(F.data.startswith("watch_"))
async def watch_anime(call: CallbackQuery):
    code = call.data.split("_")[1]
    eps = sql.execute("SELECT * FROM episodes WHERE anime_code=?", (code,)).fetchall()
    if not eps: return await call.answer("❌ Bu animening qismlari yuklanmagan!", show_alert=True)
    await call.answer("Yuklanmoqda...")
    for ep in eps:
        await call.message.answer_video(video=ep[2], caption=f"🎬 {ep[1]}")

@dp.callback_query(F.data.startswith("del_"))
async def del_anime(call: CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        code = call.data.split("_")[1]
        sql.execute("DELETE FROM anime WHERE code=?", (code,))
        sql.execute("DELETE FROM episodes WHERE anime_code=?", (code,))
        db.commit()
        await call.message.delete(); await call.answer("O'chirildi!")

# =========================
# 🚀 ISHGA TUSHIRISH
# =========================
async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
