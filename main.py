import asyncio
import sqlite3
import datetime
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# 1) Admin ID va Bot Token
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
CHANNEL = "@anime_movieuz"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ma'lumotlar bazasi
db = sqlite3.connect("anime_bot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS anime (
    code TEXT PRIMARY KEY, 
    name TEXT, 
    desc TEXT, 
    photo TEXT
)""")
cur.execute("CREATE TABLE IF NOT EXISTS parts (code TEXT, part_num INTEGER, video_id TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, join_date TEXT)")
db.commit()

# FSM (State)
class AnimeStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()
    waiting_for_desc = State()
    waiting_for_photo = State()
    waiting_for_part_code = State()
    waiting_for_videos = State()
    waiting_for_search = State()
    edit_select_code = State()
    edit_new_name = State()
    edit_new_photo = State()
    edit_new_desc = State()
    delete_code = State()

# 2) Menyular
def get_main_menu(user_id):
    kb = [[KeyboardButton(text="🔎 Anime qidirish"), KeyboardButton(text="🗂 Animelar ro'yxati")]]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_admin_menu():
    kb = [
        [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="➕ Qismlarni qo'shish")],
        [KeyboardButton(text="✏️ Animeni o'zgartirish"), KeyboardButton(text="🗑 Animeni o'chirish")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🔙 Asosiy Menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_menu():
    kb = [
        [KeyboardButton(text="✒️ Animeni nomini o'zgartirish")],
        [KeyboardButton(text="🏞 Animeni rasmini o'zgartirish")],
        [KeyboardButton(text="🎞 Animeni tavsifini o'zgartirish")],
        [KeyboardButton(text="🔙 Admin panelga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# 6) Majburiy obuna
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    args = message.text.split()
    code_from_link = args[1] if len(args) > 1 else None

    if not await is_subscribed(message.from_user.id):
        cb_data = f"check_sub_{code_from_link}" if code_from_link else "check_sub_none"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Obuna bo'lish ➕", url=f"https://t.me/{CHANNEL[1:]}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data=cb_data)]
        ])
        await message.answer("❌ Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=kb)
        return

    today = datetime.date.today().isoformat()
    cur.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (message.from_user.id, today))
    db.commit()

    if code_from_link:
        await send_anime_by_code(message, code_from_link)
    else:
        await message.answer("🔊 Xush kelibsiz! Anime tanlang.", reply_markup=get_main_menu(message.from_user.id))

@dp.callback_query(F.data.startswith("check_sub_"))
async def check_subscription_callback(call: types.CallbackQuery):
    code = call.data.replace("check_sub_", "")
    if await is_subscribed(call.from_user.id):
        today = datetime.date.today().isoformat()
        cur.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (call.from_user.id, today))
        db.commit()
        await call.message.delete()
        if code != "none":
            await send_anime_by_code(call.message, code)
        else:
            await call.message.answer("✅ Obuna tasdiqlandi! Xush kelibsiz.", reply_markup=get_main_menu(call.from_user.id))
    else:
        await call.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# 5) Admin Panel
@dp.message(F.text == "⚙️ Admin panel")
async def open_admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚙️ Admin paneliga xush kelibsiz!", reply_markup=get_admin_menu())
    else:
        await message.answer(f"🏧 Savollar yoki takliflar bo'lsa, Adminga murojaat qiling: tg://user?id={ADMIN_ID}")

@dp.message(F.text == "🔙 Asosiy Menyu")
async def back_to_main(message: types.Message):
    await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(message.from_user.id))

# 10) 📊 Statistika
@dp.message(F.text == "📊 Statistika")
async def show_statistics(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    today = datetime.date.today()
    one_day_ago = (today - datetime.timedelta(days=1)).isoformat()
    three_days_ago = (today - datetime.timedelta(days=3)).isoformat()
    seven_days_ago = (today - datetime.timedelta(days=7)).isoformat()

    cur.execute("SELECT count(*) FROM users WHERE join_date >= ?", (one_day_ago,))
    day1 = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM users WHERE join_date >= ?", (three_days_ago,))
    day3 = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM users WHERE join_date >= ?", (seven_days_ago,))
    day7 = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM anime")
    total_anime = cur.fetchone()[0]

    stats_text = (
        f"📊 **Bot Statistikasi:**\n\n"
        f"🕒 1 kun - {day1} a'zo\n"
        f"🕢 3 kun - {day3} a'zo\n"
        f"🕠 7 kun - {day7} a'zo\n"
        f"👨‍👧‍👧 Obunachilarni soni - {total_users}\n"
        f"Animelarni soni - {total_anime}"
    )
    await message.answer(stats_text, parse_mode="Markdown")

# 3) ➕ Anime qo'shish
@dp.message(F.text == "➕ Anime qo'shish")
async def add_anime_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("🍿 Yangi animening kodini kiriting:")
    await state.set_state(AnimeStates.waiting_for_code)

@dp.message(AnimeStates.waiting_for_code)
async def add_anime_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await message.answer("✒️ Animening nomini kiriting:")
    await state.set_state(AnimeStates.waiting_for_name)

@dp.message(AnimeStates.waiting_for_name)
async def add_anime_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🎞 Anime tavsifini (desc) kiriting:")
    await state.set_state(AnimeStates.waiting_for_desc)

@dp.message(AnimeStates.waiting_for_desc)
async def add_anime_desc(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("🏞 Anime uchun rasm yuboring:")
    await state.set_state(AnimeStates.waiting_for_photo)

@dp.message(AnimeStates.waiting_for_photo)
async def add_anime_photo(message: types.Message, state: FSMContext):
    photo_input = message.photo[-1].file_id if message.photo else message.text
    data = await state.get_data()
    
    cur.execute("INSERT OR REPLACE INTO anime VALUES (?, ?, ?, ?)", (data['code'], data['name'], data['desc'], photo_input))
    db.commit()
    
    bot_username = (await bot.get_me()).username
    post_link = f"https://t.me/{bot_username}?start={data['code']}"
    
    await message.answer(
        f"✅ Anime muvaffaqiyatli saqlandi!\n\n"
        f"🎬 Kanalga qo'yish uchun 'Tomosha qilish' tugmasi havolasi:\n`{post_link}`",
        reply_markup=get_admin_menu(), parse_mode="Markdown"
    )
    await state.clear()

# 12) Qismlarni ketma-ket qo'shish
@dp.message(F.text == "➕ Qismlarni qo'shish")
async def add_parts_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Qismlar qaysi anime kodiga qo'shilsin? Kodni kiriting:")
    await state.set_state(AnimeStates.waiting_for_part_code)

@dp.message(AnimeStates.waiting_for_part_code)
async def add_parts_code(message: types.Message, state: FSMContext):
    cur.execute("SELECT name FROM anime WHERE code = ?", (message.text,))
    anime = cur.fetchone()
    if not anime:
        await message.answer("❌ Bunday kodli anime topilmadi.")
        await state.clear()
        return
    
    cur.execute("SELECT COUNT(*) FROM parts WHERE code = ?", (message.text,))
    next_part = cur.fetchone()[0] + 1
    
    await state.update_data(code=message.text, next_part=next_part)
    await message.answer(f"🎬 **{anime[0]}** uchun ketma-ket qismlarni (video) yuboring.\nHozir **{next_part}-qism**ni kuting...", parse_mode="Markdown")
    await state.set_state(AnimeStates.waiting_for_videos)

@dp.message(AnimeStates.waiting_for_videos, F.video)
async def receive_anime_videos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['code']
    current_part = data['next_part']
    video_id = message.video.file_id
    
    cur.execute("INSERT INTO parts VALUES (?, ?, ?)", (code, current_part, video_id))
    db.commit()
    
    await message.answer(f"{current_part}-qism saqlandi ✅")
    next_part = current_part + 1
    await state.update_data(next_part=next_part)
    await message.answer(f"Navbatdagi **{next_part}-qism** videosini yuboring...", parse_mode="Markdown")

# 11) Qidirish
@dp.message(F.text == "🔎 Anime qidirish")
async def search_anime_start(message: types.Message, state: FSMContext):
    await message.answer("🍿 Animening kodini kiriting:")
    await state.set_state(AnimeStates.waiting_for_search)

@dp.message(AnimeStates.waiting_for_search)
async def search_anime_process(message: types.Message, state: FSMContext):
    code = message.text
    await state.clear()
    await send_anime_by_code(message, code)

# 4) Ro'yxat
@dp.message(F.text == "🗂 Animelar ro'yxati")
async def list_all_anime(message: types.Message):
    cur.execute("SELECT code, name FROM anime")
    rows = cur.fetchall()
    if not rows:
        await message.answer("Hozircha botda animelar yo'q.")
        return
    text = "🗂 **Botdagi barcha animelar ro'yxati:**\n\n"
    for r in rows:
        text += f"🔹 **{r[1]}** — Kod: `{r[0]}`\n"
    await message.answer(text, parse_mode="Markdown")

async def send_anime_by_code(message: types.Message, code: str):
    cur.execute("SELECT name, desc, photo FROM anime WHERE code = ?", (code,))
    anime = cur.fetchone()
    if not anime:
        await message.answer("❌ Anime topilmadi yoki xato kod kiritdingiz. Iltimos, boshqa kod kiriting.")
        return

    name, desc, photo = anime
    caption_text = f"🍿 **{name}**\n\nℹ️ {desc}"
    cur.execute("SELECT part_num, video_id FROM parts WHERE code = ? ORDER BY part_num ASC", (code,))
    parts = cur.fetchall()
    
    if photo:
        try: await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=caption_text, parse_mode="Markdown")
        except: await message.answer(caption_text, parse_mode="Markdown")
    else:
        await message.answer(caption_text, parse_mode="Markdown")

    if parts:
        await message.answer(f"🎬 **{name}** barcha qismlari yuklanmoqda:")
        for p in parts:
            await bot.send_video(chat_id=message.chat.id, video=p[1], caption=f"🔺 {name} - {p[0]}-qism")
    else:
        await message.answer("⚠️ Ushby animening qismlari hali yuklanmagan.")

# 9) Tahrirlash va O'chirish
@dp.message(F.text == "✏️ Animeni o'zgartirish")
async def edit_anime_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("O'zgartirmoqchi bo'lgan animengiz kodini yuboring:")
    await state.set_state(AnimeStates.edit_select_code)

@dp.message(AnimeStates.edit_select_code)
async def edit_anime_select(message: types.Message, state: FSMContext):
    cur.execute("SELECT name FROM anime WHERE code = ?", (message.text,))
    if not cur.fetchone():
        await message.answer("❌ Bunday anime topilmadi.")
        await state.clear()
        return
    await state.update_data(edit_code=message.text)
    await message.answer("Nimani o'zgartiramiz?", reply_markup=get_edit_menu())

@dp.message(F.text == "✒️ Animeni nomini o'zgartirish")
async def edit_name_prompt(message: types.Message, state: FSMContext):
    await message.answer("Yangi nomni kiriting:")
    await state.set_state(AnimeStates.edit_new_name)

@dp.message(AnimeStates.edit_new_name)
async def edit_name_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cur.execute("UPDATE anime SET name = ? WHERE code = ?", (message.text, data['edit_code']))
    db.commit()
    await message.answer("✅ Nomi o'zgartirildi!", reply_markup=get_admin_menu())
    await state.clear()

@dp.message(F.text == "🏞 Animeni rasmini o'zgartirish")
async def edit_photo_prompt(message: types.Message, state: FSMContext):
    await message.answer("Yangi rasm yuboring:")
    await state.set_state(AnimeStates.edit_new_photo)

@dp.message(AnimeStates.edit_new_photo)
async def edit_photo_save(message: types.Message, state: FSMContext):
    photo_input = message.photo[-1].file_id if message.photo else message.text
    data = await state.get_data()
    cur.execute("UPDATE anime SET photo = ? WHERE code = ?", (photo_input, data['edit_code']))
    db.commit()
    await message.answer("✅ Rasmi o'zgartirildi!", reply_markup=get_admin_menu())
    await state.clear()

@dp.message(F.text == "🎞 Animeni tavsifini o'zgartirish")
async def edit_desc_prompt(message: types.Message, state: FSMContext):
    await message.answer("Yangi tavsifni kiriting:")
    await state.set_state(AnimeStates.edit_new_desc)

@dp.message(AnimeStates.edit_new_desc)
async def edit_desc_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cur.execute("UPDATE anime SET desc = ? WHERE code = ?", (message.text, data['edit_code']))
    db.commit()
    await message.answer("✅ Tavsifi o'zgartirildi!", reply_markup=get_admin_menu())
    await state.clear()

@dp.message(F.text == "🗑 Animeni o'chirish")
async def delete_anime_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("O'chirib tashlamoqchi bo'lgan anime kodini kiriting:")
    await state.set_state(AnimeStates.delete_code)

@dp.message(AnimeStates.delete_code)
async def delete_anime_execute(message: types.Message, state: FSMContext):
    cur.execute("DELETE FROM anime WHERE code = ?", (message.text,))
    cur.execute("DELETE FROM parts WHERE code = ?", (message.text,))
    db.commit()
    await message.answer("🗑 Anime butunlay o'chirildi!", reply_markup=get_admin_menu())
    await state.clear()

@dp.message(F.text == "🔙 Admin panelga qaytish")
async def back_to_admin_panel(message: types.Message):
    await message.answer("Admin panel", reply_markup=get_admin_menu())

# --- FLASK VEB SERVER (Render port xatosini yechish uchun) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    # Flaskni alohida oqimda (Thread) yurgizamiz
    Thread(target=run_flask).start()
    # Bot pollingni boshlaymiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
