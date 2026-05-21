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

# =========================================================
# 🤖 BOT VA BAZA
# =========================================================
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

db = sqlite3.connect("anime_final_pro.db", check_same_thread=False)
sql = db.cursor()
sql.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
sql.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT PRIMARY KEY, name TEXT, desc TEXT, video_id TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS episodes(anime_code TEXT, ep_num TEXT, video TEXT)")
sql.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT PRIMARY KEY)")
db.commit()

# Boshlanishiga sening asosiy kanalingni bazaga qo'shib qo'yamiz
sql.execute("INSERT OR IGNORE INTO channels VALUES('@anime_movieuz')")
db.commit()

# =========================================================
# 🌐 VEB SERVER (24/7 ONLINE)
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

# 👑 FAQAT SENGA KO'RINADIGAN YANGI ADMIN MENU
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="➕ Qism qo'shish")],
        [KeyboardButton(text="📢 Kanallar sozlamasi"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="🗂 Animelar ro'yhati"), KeyboardButton(text="❌ Jarayonni bekor qilish")]
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

    args = message.text.split()
    code = args[1] if len(args) > 1 else None

    if not await check_sub(user_id):
        btns = []
        active_channels = sql.execute("SELECT username FROM channels").fetchall()
        for ch in active_channels:
            ch_username = ch[0]
            btns.append([InlineKeyboardButton(text=f"❌ {ch_username}", url=f"https://t.me/{ch_username.replace('@','')}")])
        cb_data = f"sub_check_{code}" if code else "sub_check_none"
        btns.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=cb_data)])
        return await message.answer("🔒 Botdan foydalanish uchun kanallarga obuna bo'ling!", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

    if code: 
        return await send_anime_direct_videos(message, code)

    if user_id == ADMIN_ID:
        if user_id in step: del step[user_id]
        return await message.answer("👋 Boshqaruv paneli yangilandi:", reply_markup=admin_menu)
        
    await message.answer("👋 Xush kelibsiz!\n🍿 Anime kodini kiriting:")

# =========================================================
# 🏗 KANAL SOZLAMALARI (FAQAT ADMIN UCHUN)
# =========================================================
step = {}
tmp = {}

@dp.message(F.text == "❌ Jarayonni bekor qilish")
async def cancel_process(m: Message):
    if m.from_user.id != ADMIN_ID: return
    uid = m.from_user.id
    if uid in step: del step[uid]
    if uid in tmp: del tmp[uid]
    await m.answer("🔄 Amallar bekor qilindi!", reply_markup=admin_menu)

@dp.message(F.text == "📢 Kanallar sozlamasi")
async def channel_settings(m: Message):
    if m.from_user.id != ADMIN_ID: return
    active_channels = sql.execute("SELECT username FROM channels").fetchall()
    
    text = "📢 <b>Hozirgi majburiy obuna kanallari:</b>\n\n"
    if not active_channels:
        text += "<i>Kanallar yo'q! Majburiy obuna o'chirilgan.</i>"
    else:
        for i, ch in enumerate(active_channels, 1):
            text += f"{i}. {ch[0]}\n"
            
    inline_btns = [
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")],
        [InlineKeyboardButton(text="🗑 Kanalni o'chirish", callback_data="del_channel")]
    ]
    await m.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_btns))

@dp.callback_query(F.data == "add_channel")
async def add_channel_callback(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    step[call.from_user.id] = "input_add_channel"
    await call.message.answer("📝 Yangi kanal usernamesini yuboring (Masalan: @yangi_kanal):")
    await call.answer()

@dp.callback_query(F.data == "del_channel")
async def del_channel_callback(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    step[call.from_user.id] = "input_del_channel"
    await call.message.answer("📝 O'chirmoqchi bo'lgan kanal usernamesini yuboring (Masalan: @eski_kanal):")
    await call.answer()

# =========================================================
# ➕ ANIME VA QISM QO'SHISH TUGMALARI
# =========================================================
@dp.message(F.text == "➕ Anime qo'shish")
async def add_a(m: Message):
    if m.from_user.id != ADMIN_ID: return
    step[m.from_user.id] = "g_code"
    await m.answer("🎬 Anime kodini kiriting (Masalan: 23):")

@dp.message(F.text == "➕ Qism qo'shish")
async def add_e(m: Message):
    if m.from_user.id != ADMIN_ID: return
    step[m.from_user.id] = "g_ep_code"
    await m.answer("Qaysi anime kodiga qism qo'shasiz? Kodni yozing:")

# =========================================================
# 🔄 ASOSIY QIDIRUV VA QADAMLARNI QAYTA ISHLASH
# =========================================================
async def send_anime(message: Message, code: str):
    data = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
    if data:
        buttons_list = [
            [InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"watch_{code}")]
        ]
        if message.from_user.id == ADMIN_ID:
            buttons_list.append([InlineKeyboardButton(text="📢 Ushbu videoli postni kanalga yuborish", callback_data=f"share_to_channel_{code}")])
            
        btn = InlineKeyboardMarkup(inline_keyboard=buttons_list)
        await bot.send_video(chat_id=message.chat.id, video=data[3], caption=f"🍿 <b>{data[1]}</b>\n\n🆔 Kod: <code>{data[0]}</code>\n\n🎞 {data[2]}", reply_markup=btn)
    else:
        if message.from_user.id == ADMIN_ID:
            await bot.send_message(message.chat.id, "❌ Bunday kodli anime topilmadi!")

async def send_anime_direct_videos(message: Message, code: str):
    eps = sql.execute("SELECT * FROM episodes WHERE anime_code=?", (code,)).fetchall()
    if not eps:
        return await bot.send_message(message.chat.id, "❌ Bu animening qismlari hali yuklanmagan!")
    for ep in eps:
        try: await bot.send_video(chat_id=message.chat.id, video=ep[2], caption=f"🎬 {ep[1]}")
        except: pass

@dp.message()
async def process_all_steps(m: Message):
    uid = m.from_user.id
    
    if uid not in step:
        if m.text and not m.text.startswith("/"): 
            await send_anime(m, m.text)
        return

    # KANAL QO'SHISH VA O'CHIRISH
    if step[uid] == "input_add_channel":
        if not m.text.startswith("@"):
            return await m.answer("❌ Kanal usernamesi @ bilan boshlanishi shart!")
        sql.execute("INSERT OR IGNORE INTO channels VALUES(?)", (m.text,))
        db.commit(); del step[uid]
        await m.answer(f"✅ {m.text} kanali qo'shildi!", reply_markup=admin_menu)

    elif step[uid] == "input_del_channel":
        sql.execute("DELETE FROM channels WHERE username=?", (m.text,))
        db.commit(); del step[uid]
        await m.answer(f"🗑 {m.text} kanali o'chirildi!", reply_markup=admin_menu)

    # ANIME QO'SHISH (VIDEO)
    elif step[uid] == "g_code":
        tmp[uid] = {"code": m.text}
        step[uid] = "g_name"; await m.answer("🍿 Anime nomini yuboring:")
    elif step[uid] == "g_name":
        tmp[uid]["name"] = m.text
        step[uid] = "g_desc"; await m.answer("🎞 Anime tavsifini yuboring:")
    elif step[uid] == "g_desc":
        tmp[uid]["desc"] = m.text
        step[uid] = "g_video"; await m.answer("🎬 Animening asosiy VIDEOSINI (Treyler) yuboring:")
    elif step[uid] == "g_video":
        if not m.video: return await m.answer("❌ Iltimos, video yuboring!")
        sql.execute("INSERT OR REPLACE INTO anime VALUES(?,?,?,?)", (tmp[uid]["code"], tmp[uid]["name"], tmp[uid]["desc"], m.video.file_id))
        db.commit(); del step[uid]; await m.answer("✅ Videoli anime muvaffaqiyatli saqlandi!", reply_markup=admin_menu)

    # QISM QO'SHISH
    elif step[uid] == "g_ep_code":
        check_exist = sql.execute("SELECT * FROM anime WHERE code=?", (m.text,)).fetchone()
        if not check_exist:
            del step[uid]
            return await m.answer("❌ Bunday kodli anime yo'q!")
        tmp[uid] = {"code": m.text}
        step[uid] = "g_ep_num"; await m.answer("Qism raqamini yuboring (Masalan: 1-qism):")
    elif step[uid] == "g_ep_num":
        tmp[uid]["num"] = m.text
        step[uid] = "g_ep_vid"; await m.answer("🎬 Videoni yuboring:")
    elif step[uid] == "g_ep_vid":
        if not m.video: return await m.answer("❌ Video yuboring!")
        sql.execute("INSERT INTO episodes VALUES(?,?,?)", (tmp[uid]["code"], tmp[uid]["num"], m.video.file_id))
        db.commit(); del step[uid]; await m.answer("✅ Qism muvaffaqiyatli qo'shildi!", reply_markup=admin_menu)

# =========================================================
# 🎛 CALLBACK HANDLERS (SHARE & WATCH)
# =========================================================
@dp.callback_query(F.data.startswith("share_to_channel_"))
async def share_to_channel_callback(call: CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        code = call.data.split("_")[3]
        data = sql.execute("SELECT * FROM anime WHERE code=?", (code,)).fetchone()
        first_ch = sql.execute("SELECT username FROM channels").fetchone()
        if not first_ch:
            return await call.answer("❌ Kanallar topilmadi!", show_alert=True)
            
        if data:
            try:
                channel_btn = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"channel_watch_{code}")]
                ])
                await bot.send_video(chat_id=first_ch[0], video=data[3], caption=f"🍿 <b>{data[1]}</b>\n\n🆔 Kod: <code>{data[0]}</code>\n\n🎞 {data[2]}", reply_markup=channel_btn)
                await call.answer("✅ Muvaffaqiyatli yuborildi!", show_alert=True)
            except Exception as e:
                await call.answer(f"❌ Xatolik: {e}", show_alert=True)

@dp.callback_query(F.data.startswith("channel_watch_"))
@dp.callback_query(F.data.startswith("watch_"))
async def watch_anime_callback(call: CallbackQuery):
    code = call.data.split("_")[-1]
    eps = sql.execute("SELECT * FROM episodes WHERE anime_code=?", (code,)).fetchall()
    if not eps: 
        return await call.answer("❌ Qismlar topilmadi!", show_alert=True)
    
    await call.answer("Qismlar yuklanmoqda...")
    for ep in eps:
        try: await bot.send_video(chat_id=call.message.chat.id, video=ep[2], caption=f"🎬 {ep[1]}")
        except: pass

@dp.message(F.text == "🗂 Animelar ro'yhati")
async def list_animes(m: Message):
    if m.from_user.id != ADMIN_ID: return
    animes = sql.execute("SELECT * FROM anime").fetchall()
    if not animes: return await m.answer("Baza bo'sh.")
    text = "🗂 Animelar:\n\n"
    for a in animes: text += f"🍿 {a[1]} - <code>{a[0]}</code>\n"
    await m.answer(text)

@dp.message(F.text == "📊 Statistika")
async def show_statistics(m: Message):
    if m.from_user.id != ADMIN_ID: return
    u = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    a = sql.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
    await m.answer(f"📊 <b>Statistika</b>\n\n👨‍👧‍👧 Jami a'zolar: {u}\n🍿 Jami animelar: {a}")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
