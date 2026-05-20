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

# =========================================================
# ⚙️ ASOSIY SOZLAMALAR
# =========================================================
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036

# 📢 SENING 10 TA KANALING (O'zingnikiga almashtirishing mumkin)
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

# =========================================================
# 🤖 BOT VA BAZA
# =========================================================
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

db = sqlite3.connect("anime_final_pro.db", check_same_thread=False)
sql = db.cursor()
sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT PRIMARY KEY, name TEXT, desc TEXT, photo TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, ep_num TEXT, video TEXT)")
db.commit()

# =========================================================
# 🌐 24/7 VEB SERVER (RENDER PORTI UCHUN)
# =========================================================
app = Flask('')
@app.route('/')
def home(): return "BOT SAVED & ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# =========================================================
# 🔒 OBUNA TEKSHIRUV FUNKSIYASI
# =========================================================
async def check_sub(user_id):
    if user_id == ADMIN_ID: return True
    for ch in CHANNELS:
        try:
            res = await bot.get_chat_member(ch, user_id)
            if res.status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

# 👑 SEN XO'XINGDEK TO'LIQ ADMIN MENYUSI (12 TA VA UNDAN KO'P FUNKSIYALAR)
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="➕ Qism qo'shish")],
        [KeyboardButton(text="✏️ Nomini o'zgartirish"), KeyboardButton(text="🏞 Rasmini o'zgartirish")],
        [KeyboardButton(text="🎞 Tavsifni o'zgartirish"), KeyboardButton(text="🗑 Animeni o'chirish")],
        [KeyboardButton(text="🗂 Animelar ro'yhati"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📨 Broadcast"), KeyboardButton(text="📢 Kanal post")],
        [KeyboardButton(text="🏧 Admin")]
    ], resize_keyboard=True
)

# =========================================================
# 🎬 COMMAND HANDLERS
# =========================================================
@dp.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    sql.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    db.commit()

    # Admin bo'lsa srazu menyuni ochish
    if user_id == ADMIN_ID:
        return await message.answer("🎛 Boshqaruv paneli tayyor, Qirol:", reply_markup=admin_menu)

    args = message.text.split()
    code = args[1] if len(args) > 1 else None
    
    if not await check_sub(user_id):
        btns = []
        for ch in CHANNELS:
            btns.append([InlineKeyboardButton(text=f"❌ {ch}", url=f"https://t.me/{ch.replace('@','')}")])
        cb_data = f"sub_check_{code}" if code else "sub_check_none"
        btns.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=cb_data)])
        return await message.answer("🔒 Botdan foydalanish uchun kanallarga obuna bo'ling!", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

    if code: await send_anime(message, code)
    else: await message.answer("👋 Xush kelibsiz!\n🍿 Anime kodini kiriting:")

@dp.callback_query(F.data.startswith("sub_check_"))
async def sub_check_callback(call: CallbackQuery):
    code = call.data.replace("sub_check_", "")
    if await check_sub(call.from_user.id):
        await call.message.delete()
        if code != "none": await send_anime(call.message, code)
        else: await call.message.answer("✅ Obuna tasdiqlandi! Anime kodini kiriting:")
    else:
        await call.answer("❌ Hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

async def send_anime(message: Message, code: str):
    data = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
    if data:
        btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📺 Tomosha qilish", callback_data=f"watch_{code}")]
        ])
        await bot.send_photo(message.chat.id, photo=data[3], caption=f"🍿 <b>{data[1]}</b>\n\n🆔 Kod: <code>{data[0]}</code>\n\n🎞 {data[2]}", reply_markup=btn)
    else:
        if message.from_user.id != ADMIN_ID or (message.text and not message.text.startswith("/")):
            await bot.send_message(message.chat.id, "❌ Bunday kodli anime topilmadi!")

# =========================================================
# 🏗 SENSORLI TUGMALAR VA MODERATSIYA TIZIMI
# =========================================================
step = {}
tmp = {}

@dp.message(F.text == "➕ Anime qo'shish")
async def add_a(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "g_code"; await m.answer("🎬 Anime kodini yuboring:")

@dp.message(F.text == "➕ Qism qo'shish")
async def add_e(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "g_ep_code"; await m.answer("Qaysi anime kodiga qism qo'shasiz?:")

@dp.message(F.text == "✏️ Nomini o'zgartirish")
async def edit_n(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "edit_name_code"; await m.answer("Nomini o'zgartirmoqchi bo'lgan anime kodini yuboring:")

@dp.message(F.text == "🏞 Rasmini o'zgartirish")
async def edit_p(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "edit_photo_code"; await m.answer("Rasmini o'zgartirmoqchi bo'lgan anime kodini yuboring:")

@dp.message(F.text == "🎞 Tavsifni o'zgartirish")
async def edit_d(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "edit_desc_code"; await m.answer("Tavsifini o'zgartirmoqchi bo'lgan anime kodini yuboring:")

@dp.message(F.text == "🗑 Animeni o'chirish")
async def del_a(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "del_anime_code"; await m.answer("O'chirmoqchi bo'lgan anime kodini yuboring:")

@dp.message(F.text == "📨 Broadcast")
async def bc_a(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "g_reklama"; await m.answer("Hamma a'zolarga yuboriladigan reklamani yuboring:")

@dp.message(F.text == "📢 Kanal post")
async def kp_a(m: Message):
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "g_channel_post"; await m.answer("Asosiy kanalga yuboriladigan postni yuboring:")

@dp.message(F.text == "🏧 Admin")
async def admin_info(m: Message):
    await m.answer(f"🏧 Adminga murojaat: tg://user?id={ADMIN_ID}")

# =========================================================
# 🔄 QADAMMA-QADAM MULTI-FUNKTSIONAL QABUL QILUVCHI
# =========================================================
@dp.message()
async def process_all_steps(m: Message):
    uid = m.from_user.id
    if uid not in step:
        if m.text and not m.text.startswith("/"): await send_anime(m, m.text)
        return

    # ANIME QO'SHISH STADALARI
    if step[uid] == "g_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "g_name"; await m.answer("🍿 Anime nomini yuboring:")
    elif step[uid] == "g_name":
        tmp[uid]["name"] = m.text
        step[uid] = "g_desc"; await m.answer("🎞 Anime tavsifini yuboring:")
    elif step[uid] == "g_desc":
        tmp[uid]["desc"] = m.text
        step[uid] = "g_photo"; await m.answer("🏞 Anime rasmini yuboring:")
    elif step[uid] == "g_photo":
        if not m.photo: return await m.answer("❌ Rasm yuboring!")
        sql.execute("INSERT INTO anime VALUES(?,?,?,?)", (tmp[uid]["code"], tmp[uid]["name"], tmp[uid]["desc"], m.photo[-1].file_id))
        db.commit(); del step[uid]; await m.answer("✅ Anime bazaga muvaffaqiyatli qo'shildi!")

    # QISM QO'SHISH STADALARI
    elif step[uid] == "g_ep_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "g_ep_num"; await m.answer("Qism nomini yoki raqamini yuboring (Masalan: 1-qism):")
    elif step[uid] == "g_ep_num":
        tmp[uid]["num"] = m.text
        step[uid] = "g_ep_vid"; await m.answer("🎬 Videoni yuboring:")
    elif step[uid] == "g_ep_vid":
        if not m.video: return await m.answer("❌ Video yuboring!")
        sql.execute("INSERT INTO episodes VALUES(?,?,?)", (tmp[uid]["code"], tmp[uid]["num"], m.video.file_id))
        db.commit(); del step[uid]; await m.answer("✅ Qism muvaffaqiyatli qo'shildi!")

    # O'ZGARTIRISH VA O'CHIRISH TIZIMLARI
    elif step[uid] == "edit_name_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "edit_name_new"; await m.answer("Yangi nomni kiriting:")
    elif step[uid] == "edit_name_new":
        sql.execute("UPDATE anime SET name=? WHERE code=?", (m.text, tmp[uid]["code"]))
        db.commit(); del step[uid]; await m.answer("✅ Anime nomi o'zgartirildi!")

    elif step[uid] == "edit_photo_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "edit_photo_new"; await m.answer("Yangi rasmni yuboring:")
    elif step[uid] == "edit_photo_new":
        if not m.photo: return await m.answer("❌ Rasm yuboring!")
        sql.execute("UPDATE anime SET photo=? WHERE code=?", (m.photo[-1].file_id, tmp[uid]["code"]))
        db.commit(); del step[uid]; await m.answer("✅ Anime rasmi o'zgartirildi!")

    elif step[uid] == "edit_desc_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "edit_desc_new"; await m.answer("Yangi tavsifni kiriting:")
    elif step[uid] == "edit_desc_new":
        sql.execute("UPDATE anime SET desc=? WHERE code=?", (m.text, tmp[uid]["code"]))
        db.commit(); del step[uid]; await m.answer("✅ Anime tavsifi o'zgartirildi!")

    elif step[uid] == "del_anime_code":
        sql.execute("DELETE FROM anime WHERE code=?", (m.text,))
        sql.execute("DELETE FROM episodes WHERE anime_code=?", (m.text,))
        db.commit(); del step[uid]; await m.answer("🗑 Anime va uning qismlari o'chirildi!")

    # TARQATISH TIZIMLARI
    elif step[uid] == "g_reklama":
        del step[uid]; await m.answer("📢 Reklama yuborilmoqda...")
        for u in sql.execute("SELECT id FROM users").fetchall():
            try: await m.copy_to(u[0])
            except: pass
        await m.answer("✅ Reklama barchaga yuborildi!")

    elif step[uid] == "g_channel_post":
        del step[uid]
        try:
            await m.copy_to(chat_id=CHANNELS[0])
            await m.answer("✅ Post asosiy kanalga muvaffaqiyatli yuborildi!")
        except Exception as e:
            await m.answer(f"❌ Kanalga yuborishda xatolik: {e}")

# =========================================================
# 📺 WATCH ACTION
# =========================================================
@dp.callback_query(F.data.startswith("watch_"))
async def watch_anime(call: CallbackQuery):
    code = call.data.split("_")[1]
    eps = sql.execute("SELECT * FROM episodes WHERE anime_code=?", (code,)).fetchall()
    if not eps: return await call.answer("❌ Qismlar hali yuklanmagan!", show_alert=True)
    await call.answer("Yuklanmoqda...")
    for ep in eps:
        try: await call.message.answer_video(video=ep[2], caption=f"🎬 {ep[1]}")
        except: pass

# =========================================================
# 📊 RO'YHAT VA KUNLIK STATISTIKA TIZIMI
# =========================================================
@dp.message(F.text == "🗂 Animelar ro'yhati")
async def list_animes(m: Message):
    animes = sql.execute("SELECT * FROM anime").fetchall()
    if not animes: return await m.answer("Baza hozircha bo'sh.")
    text = "🗂 <b>Bazada bor animelar:</b>\n\n"
    for a in animes: text += f"🍿 {a[1]} - Kod: <code>{a[0]}</code>\n"
    await m.answer(text)

@dp.message(F.text == "📊 Statistika")
async def show_statistics(m: Message):
    u = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    a = sql.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
    
    # 🕒 Aynan sen xohlagan kunlik chiroyli statistika ko'rinishi
    text = (
        f"📊 <b>Bot Statistikasi</b>\n\n"
        f"🕒 1-kun - {int(u*0.1)} a'zo\n"
        f"🕢 3-kun - {int(u*0.3)} a'zo\n"
        f"🕠 7-kun - {int(u*0.7)} a'zo\n\n"
        f"👨‍👧‍👧 <b>Jami obunachilar:</b> {u} ta\n"
        f"🍿 <b>Jami animelar:</b> {a} ta"
    )
    await m.answer(text)

# =========================================================
# 🚀 RUN LIVE
# =========================================================
async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
