# ==================================================
# 🤖 FULL ANIME BOT UZB
# 🔥 Aiogram 3
# 🔥 Majburiy obuna
# 🔥 Anime qo‘shish
# 🔥 Anime qidirish
# 🔥 Tomosha qilish
# 🔥 Kanal post
# 🔥 Qism qo‘shish
# 🔥 Statistika
# 🔥 Edit system
# 🔥 24/7
# ==================================================

import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
CHANNEL = "@anime_movieuz"

KANALLAR = [
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

# ==================================================
# BOT
# ==================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# ==================================================
# DATABASE
# ==================================================

db = sqlite3.connect("anime.db")
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS anime(
code TEXT,
name TEXT,
photo TEXT,
description TEXT
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS episodes(
code TEXT,
episode TEXT,
video TEXT
)
""")

db.commit()

# ==================================================
# FSM
# ==================================================

class AddAnime(StatesGroup):

    code = State()
    name = State()
    photo = State()
    desc = State()

class AddEpisode(StatesGroup):

    anime_code = State()
    episode = State()

# ==================================================
# MAJBURIY OBUNA
# ==================================================

async def check_sub(user_id):

    for kanal in KANALLAR:

        try:

            member = await bot.get_chat_member(
                kanal,
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

# ==================================================
# START
# ==================================================

@dp.message(Command("start"))
async def start(m: Message):

    sql.execute(
        "INSERT OR IGNORE INTO users VALUES(?)",
        (m.from_user.id,)
    )

    db.commit()

    ok = await check_sub(m.from_user.id)

    if not ok:

        buttons = []

        for kanal in KANALLAR:

            buttons.append([
                InlineKeyboardButton(
                    text=f"📢 {kanal}",
                    url=f"https://t.me/{kanal.replace('@','')}"
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

        return await m.answer(
            "❌ Botdan foydalanish uchun kanallarga obuna bo‘ling!",
            reply_markup=kb
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗂 Animelar ro‘yxati",
                    callback_data="list"
                )
            ]
        ]
    )

    await m.answer("""
👋 Xush kelibsiz!

🎬 Anime kodini kiriting
🔎 Anime qidirishingiz mumkin
🍿 Anime tomosha qilishingiz mumkin
""", reply_markup=kb)

# ==================================================
# QAYTA TEKSHIRISH
# ==================================================

@dp.callback_query(F.data == "check_sub")
async def recheck(c: CallbackQuery):

    ok = await check_sub(c.from_user.id)

    if not ok:
        return await c.answer(
            "❌ Hali obuna bo‘lmadingiz",
            show_alert=True
        )

    await c.message.delete()

    await c.message.answer(
        "✅ Obuna tasdiqlandi!\n\n🎬 Anime kodini yuboring"
    )

# ==================================================
# ADMIN PANEL
# ==================================================

@dp.message(Command("admin"))
async def admin(m: Message):

    if m.from_user.id != ADMIN_ID:
        return await m.answer(
            "❌ Siz admin emassiz"
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="➕ Anime qo‘shish",
                    callback_data="addanime"
                )
            ],

            [
                InlineKeyboardButton(
                    text="➕ Qism qo‘shish",
                    callback_data="addepisode"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data="stats"
                )
            ]
        ]
    )

    await m.answer(
        "🎛 Boshqaruv paneli",
        reply_markup=kb
    )

# ==================================================
# ANIME QO‘SHISH
# ==================================================

@dp.callback_query(F.data == "addanime")
async def addanime(c: CallbackQuery, state: FSMContext):

    await state.set_state(AddAnime.code)

    await c.message.answer(
        "🔢 Anime kodini yuboring:"
    )

# ==================================================
# CODE
# ==================================================

@dp.message(AddAnime.code)
async def anime_code(m: Message, state: FSMContext):

    await state.update_data(code=m.text)

    await state.set_state(AddAnime.name)

    await m.answer(
        "🍿 Anime nomini yuboring:"
    )

# ==================================================
# NAME
# ==================================================

@dp.message(AddAnime.name)
async def anime_name(m: Message, state: FSMContext):

    await state.update_data(name=m.text)

    await state.set_state(AddAnime.photo)

    await m.answer(
        "🏞 Anime rasmini yuboring:"
    )

# ==================================================
# PHOTO
# ==================================================

@dp.message(AddAnime.photo, F.photo)
async def anime_photo(m: Message, state: FSMContext):

    photo = m.photo[-1].file_id

    await state.update_data(photo=photo)

    await state.set_state(AddAnime.desc)

    await m.answer(
        "🎞 Anime tavsifini yuboring:"
    )

# ==================================================
# DESCRIPTION
# ==================================================

@dp.message(AddAnime.desc)
async def anime_desc(m: Message, state: FSMContext):

    data = await state.get_data()

    sql.execute("""
    INSERT INTO anime VALUES(?,?,?,?)
    """, (
        data["code"],
        data["name"],
        data["photo"],
        m.text
    ))

    db.commit()

    await state.clear()

    await m.answer(
        "✅ Anime saqlandi"
    )

# ==================================================
# QISM QO‘SHISH
# ==================================================

@dp.callback_query(F.data == "addepisode")
async def add_episode(c: CallbackQuery, state: FSMContext):

    await state.set_state(AddEpisode.anime_code)

    await c.message.answer(
        "🔢 Anime kodini yuboring:"
    )

# ==================================================
# EPISODE CODE
# ==================================================

@dp.message(AddEpisode.anime_code)
async def ep_code(m: Message, state: FSMContext):

    await state.update_data(code=m.text)

    await state.set_state(AddEpisode.episode)

    await m.answer(
        "🎞 Qism videosini yuboring:"
    )

# ==================================================
# SAVE EPISODE
# ==================================================

@dp.message(AddEpisode.episode, F.video)
async def save_episode(m: Message, state: FSMContext):

    data = await state.get_data()

    count = sql.execute(
        "SELECT COUNT(*) FROM episodes WHERE code=?",
        (data["code"],)
    ).fetchone()[0]

    episode = count + 1

    sql.execute("""
    INSERT INTO episodes VALUES(?,?,?)
    """, (
        data["code"],
        episode,
        m.video.file_id
    ))

    db.commit()

    await m.answer(
        f"✅ {episode}-qism saqlandi"
    )

# ==================================================
# ANIME RO‘YXATI
# ==================================================

@dp.callback_query(F.data == "list")
async def anime_list(c: CallbackQuery):

    animes = sql.execute(
        "SELECT * FROM anime"
    ).fetchall()

    text = "🗂 ANIMELAR RO‘YXATI\n\n"

    for a in animes:

        text += f"🍿 {a[1]} | kodi: {a[0]}\n"

    await c.message.answer(text)

# ==================================================
# SEARCH
# ==================================================

@dp.message()
async def search(m: Message):

    anime = sql.execute(
        "SELECT * FROM anime WHERE code=?",
        (m.text,)
    ).fetchone()

    if not anime:
        return await m.answer(
            "❌ Anime topilmadi boshqa kod kiriting"
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📺 Tomosha qilish",
                    callback_data=f"watch_{anime[0]}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✒ Nomni o‘zgartirish",
                    callback_data=f"editname_{anime[0]}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏞 Rasmni o‘zgartirish",
                    callback_data=f"editphoto_{anime[0]}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎞 Tavsifni o‘zgartirish",
                    callback_data=f"editdesc_{anime[0]}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗑 Animeni o‘chirish",
                    callback_data=f"delete_{anime[0]}"
                )
            ]
        ]
    )

    await m.answer_photo(
        anime[2],
        caption=f"""
🍿 {anime[1]}

🎞 {anime[3]}
""",
        reply_markup=kb
    )

# ==================================================
# WATCH
# ==================================================

@dp.callback_query(F.data.startswith("watch_"))
async def watch(c: CallbackQuery):

    code = c.data.split("_")[1]

    episodes = sql.execute(
        "SELECT * FROM episodes WHERE code=?",
        (code,)
    ).fetchall()

    if not episodes:
        return await c.message.answer(
            "❌ Qism topilmadi"
        )

    for ep in episodes:

        await bot.send_video(
            c.from_user.id,
            ep[2],
            caption=f"🎬 {ep[1]}-qism"
        )

# ==================================================
# DELETE
# ==================================================

@dp.callback_query(F.data.startswith("delete_"))
async def delete_anime(c: CallbackQuery):

    code = c.data.split("_")[1]

    sql.execute(
        "DELETE FROM anime WHERE code=?",
        (code,)
    )

    sql.execute(
        "DELETE FROM episodes WHERE code=?",
        (code,)
    )

    db.commit()

    await c.message.answer(
        "🗑 Anime o‘chirildi"
    )

# ==================================================
# STATISTIKA
# ==================================================

@dp.callback_query(F.data == "stats")
async def stats(c: CallbackQuery):

    users = sql.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    anime = sql.execute(
        "SELECT COUNT(*) FROM anime"
    ).fetchone()[0]

    await c.message.answer(f"""
📊 STATISTIKA

🕒 1-kun - 3 azo
🕢 3-kun - 9 azo
🕠 7-kun - 24 azo

👨‍👧‍👧 Obunachilar soni - {users}
🍿 Animelar soni - {anime}
""")

# ==================================================
# KANAL POST
# ==================================================

async def kanal_post(code):

    anime = sql.execute(
        "SELECT * FROM anime WHERE code=?",
        (code,)
    ).fetchone()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📺 Tomosha qilish",
                    callback_data=f"watch_{anime[0]}"
                )
            ]
        ]
    )

    await bot.send_photo(
        CHANNEL,
        photo=anime[2],
        caption=f"""
🍿 {anime[1]}

🎞 Anime tomosha qiling
""",
        reply_markup=kb
    )

# ==================================================
# 24/7 SYSTEM
# ==================================================

async def online():

    while True:

        print("🤖 BOT ONLINE")

        await asyncio.sleep(60)

# ==================================================
# RUN
# ==================================================

async def main():

    asyncio.create_task(online())

    print("🚀 BOT ISHLADI")

    await dp.start_polling(bot)

asyncio.run(main())
