import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Sozlamalar
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
CHANNEL = "@anime_movieuz"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Baza
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS anime (code TEXT PRIMARY KEY, name TEXT, desc TEXT, photo TEXT, file_id TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
db.commit()

# Holatlar (FSM)
class AddAnime(StatesGroup):
    code = State(); name = State(); desc = State(); photo = State(); file_id = State()

# Menyular
def get_menu(uid):
    kb = [[KeyboardButton(text="🔎 Anime qidirish"), KeyboardButton(text="🗂 Animelar ro'yxati")]]
    if uid == ADMIN_ID: kb.append([KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="📊 Statistika")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Majburiy obuna
async def is_sub(uid):
    try: return (await bot.get_chat_member(chat_id=CHANNEL, user_id=uid)).status in ['member', 'administrator', 'creator']
    except: return False

@dp.message(Command("start"))
async def start(msg: types.Message):
    if not await is_sub(msg.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Obuna bo'lish ➕", url=f"https://t.me/{CHANNEL[1:]}"), InlineKeyboardButton(text="✅ Tekshirish", callback_data="check")]])
        await msg.answer("Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=kb)
    else:
        cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (msg.from_user.id,)); db.commit()
        await msg.answer("Xush kelibsiz! Anime tanlang.", reply_markup=get_menu(msg.from_user.id))

@dp.callback_query(F.data == "check")
async def check(call: types.CallbackQuery):
    if await is_sub(call.from_user.id):
        await call.message.edit_text("Obuna tasdiqlandi! Xush kelibsiz.", reply_markup=get_menu(call.from_user.id))
    else:
        await call.answer("Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)

# Statistika
@dp.message(F.text == "📊 Statistika", F.from_user.id == ADMIN_ID)
async def stats(msg: types.Message):
    cur.execute("SELECT count(*) FROM users"); u = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM anime"); a = cur.fetchone()[0]
    await msg.answer(f"👨‍👧‍👧 Obunachilar: {u}\n🎬 Animelar soni: {a}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
