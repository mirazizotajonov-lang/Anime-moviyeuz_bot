import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
CHANNEL = "@anime_movieuz"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Baza
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS anime (code TEXT PRIMARY KEY, name TEXT, desc TEXT, photo TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
db.commit()

# FSM (State) - Kino qoshish uchun
class AddAnime(StatesGroup):
    code = State()
    name = State()
    desc = State()
    photo = State()

# 1. Boshqaruv paneli tugmalari
def get_main_menu(user_id):
    kb = [[KeyboardButton(text="🔎 Anime qidirish"), KeyboardButton(text="🗂 Animelar ro'yxati")]]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="📊 Statistika")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# 6. Majburiy obuna
async def is_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

@dp.message(Command("start"))
async def start(message: types.Message):
    if not await is_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Obuna bo'lish ➕", url=f"https://t.me/{CHANNEL[1:]}"), InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]])
        await message.answer("Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=kb)
    else:
        cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
        db.commit()
        await message.answer("Xush kelibsiz! Anime tanlang.", reply_markup=get_main_menu(message.from_user.id))

# Statistika (10-band)
@dp.message(F.text == "📊 Statistika")
async def stats(message: types.Message):
    cur.execute("SELECT count(*) FROM users")
    u_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM anime")
    a_count = cur.fetchone()[0]
    await message.answer(f"👨‍👧‍👧 Obunachilar: {u_count}\n🎬 Animelar soni: {a_count}")

# Kino qo'shish (3-band)
@dp.message(F.text == "➕ Kino qo'shish")
async def add_start(message: types.Message, state: FSMContext):
    await message.answer("Kino kodini kiriting:")
    await state.set_state(AddAnime.code)

@dp.message(AddAnime.code)
async def add_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await message.answer("Kino nomini yuboring:")
    await state.set_state(AddAnime.name)

# ... (Bu yerga davomini qo'shish kerak, chunki kod juda uzun)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
