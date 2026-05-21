import asyncio
import sqlite3
import os
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import *
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# =========================================================
# ⚙️ ASOSIY SOZLAMALAR (YANGI TOKEN JOYLANDI)
# =========================================================
TOKEN = "8896986389:AAGDPa1G55w5z8bSOVGzBN2e2cronMTRNJ0"
ADMIN_ID = 7164685036

# =========================================================
# 🤖 BOT VA BAZA TIZIMI
# =========================================================
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

db = sqlite3.connect("anime_final_clean.db", check_same_thread=False)
sql = db.cursor()
sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT PRIMARY KEY, name TEXT, desc TEXT, video_id TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, ep_num TEXT, video TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT PRIMARY KEY)")
db.commit()

# Boshlanishiga sening kanalingni bazaga kiritib qo'yamiz
sql.execute("INSERT OR IGNORE INTO channels VALUES('@anime_movieuz')")
db.commit()

# =========================================================
# 🌐 WEB SERVER (24/7 ONLINE TURISHI UCHUN)
# =========================================================
app = Flask('')
@app.route('/')
def home(): return "BOT ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# =========================================================
# 🔒 MAJBURIY OBUNA TEKSHIRUVI
# =========================================================
async def check_sub(user_id):
    if user_id == ADMIN_ID: return True
    active_channels = sql.execute("SELECT username FROM channels").fetchall()
    for ch in active_channels:
        ch_username = ch[0]
        try:
            res = await bot.get_chat_member(ch_username, user_id)
            if res.status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

# =========================================================
# 👑 KLAVIATURALAR (KEYBOARDS)
# =========================================================

# Adminlar uchun boshqaruv paneli (Sening hamma eski tugmalaring joyida)
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="➕ Qism qo'shish")],
        [KeyboardButton(text="✏️ Nomini o'zgartirish"), KeyboardButton(text="🏞 Rasmini o'zgartirish")],
        [KeyboardButton(text="📝 Tavsifni o'zgartirish"), KeyboardButton(text="🗑 Animeni o'chirish")],
        [KeyboardButton(text="📢 Kanallar sozlamasi"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="🗂 Animelar ro'yhati"), KeyboardButton(text="📨 Broadcast")],
        [KeyboardButton(text="❌ Jarayonni bekor qilish")]
    ], resize_keyboard=True
)

# Oddiy foydalanuvchilar uchun chiqadigan tugma
user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏪 Admin")]
    ], resize_keyboard=True
)

step = {}
tmp = {}

# =========================================================
# 🎬 BUYRUQLAR (COMMANDS)
# =========================================================
@dp.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    sql.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    db.commit()
    
    if user_id in step: del step[user_id]

    # Majburiy obunani tekshirish
    if not await check_sub(user_id):
        btns = []
        active_channels = sql.execute("SELECT username FROM channels").fetchall()
        for ch in active_channels:
            ch_username = ch[0]
            btns.append([InlineKeyboardButton(text=f"❌ {ch_username}", url=f"https://t.me/{ch_username.replace('@','')}")])
        btns.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="sub_check_now")])
        return await message.answer("🔒 Botdan foydalanish uchun kanallarga obuna bo'ling!", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
    
    if user_id == ADMIN_ID:
        return await message.answer("👋 Xush kelibsiz, Admin!\nBoshqaruv paneli tayyor:", reply_markup=admin_menu)
    
    await message.answer("👋 Xush kelibsiz!\n🍿 Anime kodini kiriting:", reply_markup=user_menu)

@dp.callback_query(F.data == "sub_check_now")
async def sub_check_callback(call: CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        if call.from_user.id == ADMIN_ID:
            await call.message.answer("👋 Xush kelibsiz, Admin!", reply_markup=admin_menu)
        else:
            await call.message.answer("✅ Obuna tasdiqlandi! Anime kodini kiriting:", reply_markup=user_menu)
    else:
        await call.answer("❌ Hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

# =========================================================
# 🛠 ADMIN TUGMALARINI BOSGANDAGI AMALLAR
# =========================================================
@dp.message(F.text == "❌ Jarayonni bekor qilish")
async def cancel_process(m: Message):
    if m.from_user.id != ADMIN_ID: return
    uid = m.from_user.id
    if uid in step: del step[uid]
    await m.answer("🔄 Barcha amallar bekor qilindi!", reply_markup=admin_menu)

@dp.message(F.text == "📊 Statistika")
async def show_statistics(m: Message):
    if m.from_user.id != ADMIN_ID: return
    u = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    a = sql.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
    await m.answer(f"📊 <b>Statistika:</b>\n\n👨‍👧‍👧 Jami a'zolar: {u}\n🍿 Jami animelar: {a}")

@dp.message(F.text == "🗂 Animelar ro'yhati")
async def list_animes(m: Message):
    if m.from_user.id != ADMIN_ID: return
    animes = sql.execute("SELECT * FROM anime").fetchall()
    if not animes: return await m.answer("Baza bo'sh.")
    text = "🗂 <b>Bazada bor animelar:</b>\n\n"
    for a in animes: text += f"🍿 {a[1]} - Kod: <code>{a[0]}</code>\n"
    await m.answer(text)

@dp.message(F.text == "📢 Kanallar sozlamasi")
async def channel_settings(m: Message):
    if m.from_user.id != ADMIN_ID: return
    ch = sql.execute("SELECT username FROM channels").fetchall()
    text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
    for i, c in enumerate(ch, 1): text += f"{i}. {c[0]}\n"
    
    btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")],
        [InlineKeyboardButton(text="🗑 Kanalni o'chirish", callback_data="del_channel")]
    ])
    await m.answer(text, reply_markup=btn)

@dp.message(F.text == "➕ Anime qo'shish")
async def a1(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "a_code"; await m.answer("🎬 Yangi anime uchun KOD kiriting (Masalan: 23):")

@dp.message(F.text == "➕ Qism qo'shish")
async def a2(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "e_code"; await m.answer("Qaysi anime kodiga qism qo'shasiz? Kodni yozing:")

@dp.message(F.text == "✏️ Nomini o'zgartirish")
async def a3(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "edit_name_code"; await m.answer("Nomini o'zgartirmoqchi bo'lgan anime kodini kiriting:")

@dp.message(F.text == "🏞 Rasmini o'zgartirish")
async def a4(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "edit_pic_code"; await m.answer("Videosini o'zgartirmoqchi bo'lgan anime kodini kiriting:")

@dp.message(F.text == "📝 Tavsifni o'zgartirish")
async def a5(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "edit_desc_code"; await m.answer("Tavsifini o'zgartirmoqchi bo'lgan anime kodini kiriting:")

@dp.message(F.text == "🗑 Animeni o'chirish")
async def a6(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "del_anime_code"; await m.answer("O'chirib tashlamoqchi bo'lgan anime kodini kiriting:")

@dp.message(F.text == "📨 Broadcast")
async def a7(m: Message): 
    if m.from_user.id == ADMIN_ID: step[m.from_user.id] = "broad_text"; await m.answer("Hamma foydalanuvchilarga yuboriladigan xabar matnini yozing:")

# =========================================================
# 🔄 INLINE CALLBACKS (KANAL SOZLAMALARI)
# =========================================================
@dp.callback_query(F.data == "add_channel")
async def add_ch_cb(call: CallbackQuery):
    step[call.from_user.id] = "add_ch"
    await call.message.answer("📝 Yangi kanal usernamesini yuboring (Masalan: @anime_movieuz):")
    await call.answer()

@dp.callback_query(F.data == "del_channel")
async def del_ch_cb(call: CallbackQuery):
    step[call.from_user.id] = "del_ch"
    await call.message.answer("📝 O'chirmoqchi bo'lgan kanal usernamesini yuboring:")
    await call.answer()

# =========================================================
# 🔄 MATNLARNI FILTRLASH (ZANJIRLI XATOSIZ TIZIM)
# =========================================================
@dp.message()
async def main_handler(m: Message):
    uid = m.from_user.id
    
    # ODDY FOYDALANUVCHILAR ADMIN TUGMASINI BOSGANDA
    if m.text == "🏪 Admin":
        btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👑 Admin bilan bog'lanish", url="https://t.me/mirazizotajonov_lang")]
        ])
        return await m.answer("👨‍💻 Bot admini bilan bog'lanish uchun quyidagi tugmani bosing:", reply_markup=btn)

    # AGAR FOYDALANUVCHI AMAL USTIDA BO'LMASA - ANIME QIDIRADI
    if uid not in step:
        if m.text and not m.text.startswith("/"):
            data = sql.execute("SELECT * FROM anime WHERE code=?", (m.text,)).fetchone()
            if data:
                if uid == ADMIN_ID:
                    btn = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"watch_{m.text}")],
                        [InlineKeyboardButton(text="📢 Kanalga post yuborish", callback_data=f"send_ch_{m.text}")]
                    ])
                else:
                    btn = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"watch_{m.text}")]
                    ])
                await m.answer_video(video=data[3], caption=f"🍿 <b>{data[1]}</b>\n\n🆔 Kod: <code>{data[0]}</code>\n\n🎞 {data[2]}", reply_markup=btn)
            else:
                if uid == ADMIN_ID:
                    await m.answer("❌ Bunday kodli anime topilmadi!")
        return

    # KANAL QO'SHISH VA O'CHIRISH
    if step[uid] == "add_ch":
        if not m.text.startswith("@"): return await m.answer("❌ Username @ bilan boshlanishi shart!")
        sql.execute("INSERT OR IGNORE INTO channels VALUES(?)", (m.text,))
        db.commit(); del step[uid]
        return await m.answer("✅ Kanal majburiy obunaga qo'shildi!", reply_markup=admin_menu)
    elif step[uid] == "del_ch":
        sql.execute("DELETE FROM channels WHERE username=?", (m.text,))
        db.commit(); del step[uid]
        return await m.answer("🗑 Kanal ro'yxatdan o'chirildi!", reply_markup=admin_menu)

    # BROADCAST (REKLAMA)
    elif step[uid] == "broad_text":
        del step[uid]
        await m.answer("🚀 Xabar yuborish boshlandi...")
        users = sql.execute("SELECT id FROM users").fetchall()
        count = 0
        for u in users:
            try:
                await bot.send_message(chat_id=u[0], text=m.text)
                count += 1
            except: pass
        return await m.answer(f"✅ Xabar {count}ta foydalanuvchiga muvaffaqiyatli yetkazildi!", reply_markup=admin_menu)

    # ANIME QO'SHISH
    elif step[uid] == "a_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "a_name"; return await m.answer("🍿 Anime nomini yuboring:")
    elif step[uid] == "a_name":
        tmp[uid]["name"] = m.text
        step[uid] = "a_desc"; return await m.answer("🎞 Anime tavsifini yuboring:")
    elif step[uid] == "a_desc":
        tmp[uid]["desc"] = m.text
        step[uid] = "a_vid"; return await m.answer("🎬 Animening asosiy VIDEOSINI (Treyler) yuboring:")
    elif step[uid] == "a_vid":
        if not m.video: return await m.answer("❌ Iltimos, video formatida yuboring!")
        sql.execute("INSERT OR REPLACE INTO anime VALUES(?,?,?,?)", (tmp[uid]["code"], tmp[uid]["name"], tmp[uid]["desc"], m.video.file_id))
        db.commit(); del step[uid]
        return await m.answer("✅ Videoli anime muvaffaqiyatli saqlandi!", reply_markup=admin_menu)

    # QISM QO'SHISH
    elif step[uid] == "e_code":
        check = sql.execute("SELECT * FROM anime WHERE code=?", (m.text,)).fetchone()
        if not check: del step[uid]; return await m.answer("❌ Bunday kodli anime yo'q!", reply_markup=admin_menu)
        tmp[uid] = {"code": m.text}
        step[uid] = "e_num"; return await m.answer("Qism raqamini yuboring (Masalan: 1-qism):")
    elif step[uid] == "e_num":
        tmp[uid]["num"] = m.text
        step[uid] = "e_vid"; return await m.answer("🎬 Qism videosini yuboring:")
    elif step[uid] == "e_vid":
        if not m.video: return await m.answer("❌ Iltimos, video yuboring!")
        sql.execute("INSERT INTO episodes VALUES(?,?,?)", (tmp[uid]["code"], tmp[uid]["num"], m.video.file_id))
        db.commit(); del step[uid]
        return await m.answer("✅ Qism muvaffaqiyatli qo'shildi!", reply_markup=admin_menu)

    # TAHRIRLASH (EDITING)
    elif step[uid] == "edit_name_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "edit_name_new"; return await m.answer("📝 Yangi nomini yuboring:")
    elif step[uid] == "edit_name_new":
        sql.execute("UPDATE anime SET name=? WHERE code=?", (m.text, tmp[uid]["code"]))
        db.commit(); del step[uid]; return await m.answer("✅ Anime nomi o'zgartirildi!", reply_markup=admin_menu)

    elif step[uid] == "edit_pic_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "edit_pic_new"; return await m.answer("🎬 Yangi asosiy videoni yuboring:")
    elif step[uid] == "edit_pic_new":
        if not m.video: return await m.answer("❌ Iltimos, video yuboring!")
        sql.execute("UPDATE anime SET video_id=? WHERE code=?", (m.video.file_id, tmp[uid]["code"]))
        db.commit(); del step[uid]; return await m.answer("✅ Anime videosi yangilandi!", reply_markup=admin_menu)

    elif step[uid] == "edit_desc_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "edit_desc_new"; return await m.answer("📝 Yangi tavsif matnini yuboring:")
    elif step[uid] == "edit_desc_new":
        sql.execute("UPDATE anime SET desc=? WHERE code=?", (m.text, tmp[uid]["code"]))
        db.commit(); del step[uid]; return await m.answer("✅ Anime tavsifi o'zgartirildi!", reply_markup=admin_menu)

    elif step[uid] == "del_anime_code":
        sql.execute("DELETE FROM anime WHERE code=?", (m.text,))
        sql.execute("DELETE FROM episodes WHERE anime_code=?", (m.text,))
        db.commit(); del step[uid]; return await m.answer("🗑 Anime o'chirib tashlandi!", reply_markup=admin_menu)

# =========================================================
# 🎛 CALLBACK PROCESSING (POSTING & WATCHING)
# =========================================================
@dp.callback_query(F.data.startswith("send_ch_"))
async def send_to_channel_cb(call: CallbackQuery):
    code = call.data.replace("send_ch_", "")
    data = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
    ch = sql.execute("SELECT username FROM channels").fetchone()
    
    if not ch: return await call.answer("❌ Avval Kanallar sozlamasidan kanal qo'shing!", show_alert=True)
    if data:
        try:
            btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"watch_{code}")]])
            await bot.send_video(chat_id=ch[0], video=data[3], caption=f"🍿 <b>{data[1]}</b>\n\n🆔 Kod: <code>{data[0]}</code>\n\n🎞 {data[2]}", reply_markup=btn)
            await call.answer("✅ Videoli post kanalga muvaffaqiyatli yuborildi!", show_alert=True)
        except Exception as e:
            await call.answer(f"❌ Xatolik: {e}", show_alert=True)

@dp.callback_query(F.data.startswith("watch_"))
async def watch_anime_cb(call: CallbackQuery):
    code = call.data.replace("watch_", "")
    eps = sql.execute("SELECT * FROM episodes WHERE anime_code=?", (code,)).fetchall()
    if not eps: return await call.answer("❌ Qismlar hali yuklanmagan!", show_alert=True)
    
    await call.answer("Qismlar yuborilmoqda...")
    for ep in eps:
        try: await bot.send_video(chat_id=call.message.chat.id, video=ep[2], caption=f"🎬 {ep[1]}")
        except: pass

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
