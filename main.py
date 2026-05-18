import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta

# 🤖 YANGI BOT TOKEN VA ADMIN ID
TOKEN = "8838566303:AAGO7eZsB8aNXsDwdGRrY6kW-SVDGx0NHV4"
ADMIN_ID = 7164685036
KANAL_USERNAME = "@anime_movieuz"

bot = telebot.TeleBot(TOKEN)

# 💾 BAZANI SOZLASh
def init_db():
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, join_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS animes 
                      (kod TEXT PRIMARY KEY, nomi TEXT, rasm TEXT, tavsif TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS qismlar 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, anime_kod TEXT, qism_raqam INTEGER, video_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# 🔊 TAYYOR SO'ZLAR
SOZ_SALOM = "👋 Salom! Botimizga xush kelibsiz.\n🍿 Animelarni ko'rish uchun kanalimizga obuna bo'ling va anime kodini kiriting!"
SOZ_TOPILMADI = "❌ Kechirasiz, bunday kodli anime topilmadi. Kodni to'g'ri kiritganingizni tekshiring."
SOZ_MAJBURIY = f"⚠️ Botdan foydalanish uchun rasmiy kanalimizga obuna bo'ling:\n{KANAL_USERNAME}\n\nObuna bo'lib, qayta /start bosing."

# 🔒 MAJBURIY OBUNA TEKSHIRISH
def check_sub(user_id):
    try:
        member = bot.get_chat_member(KANAL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return True

# 🎛 ADMIN REPLIY MENYU
def admin_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("📊 Statistika"), types.KeyboardButton("🎬 Anime qidirish"))
    markup.add(types.KeyboardButton("📂 Anime ro'yxati"), types.KeyboardButton("➕ Anime qo'shish"))
    markup.add(types.KeyboardButton("➕ Qism qo'shish"), types.KeyboardButton("📤 Kanal post"))
    markup.add(types.KeyboardButton("🏧 Admin bilan aloqa"))
    return markup

# 🎛 INLINE TUGMALAR
def inline_boshqaruv_baneri(anime_kod):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📦 Qismlar", callback_data=f"view_qismlar_{anime_kod}"),
        types.InlineKeyboardButton("📝 Nomni o'zgartirish", callback_data=f"edit_name_{anime_kod}"),
        types.InlineKeyboardButton("📝 Tavsifni o'zgartirish", callback_data=f"edit_desc_{anime_kod}"),
        types.InlineKeyboardButton("📝 Rasmini o'zgartirish", callback_data=f"edit_pic_{anime_kod}"),
        types.InlineKeyboardButton("🗑 Animeni o'chirish", callback_data=f"delete_{anime_kod}"),
        types.InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)", 
                   (user_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

    if not check_sub(user_id) and user_id != ADMIN_ID:
        bot.send_message(user_id, SOZ_MAJBURIY)
        return

    text = message.text.split()
    if len(text) > 1:
        anime_kod = text[1]
        show_anime_to_user(user_id, anime_kod)
        return

    if user_id == ADMIN_ID:
        bot.send_message(user_id, "👑 Xush kelibsiz, Admin!", reply_markup=admin_menu())
    else:
        bot.send_message(user_id, SOZ_SALOM)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text

    if not check_sub(user_id) and user_id != ADMIN_ID:
        bot.send_message(user_id, SOZ_MAJBURIY)
        return

    if user_id == ADMIN_ID:
        if text == "📊 Statistika":
            show_statistics(user_id)
        elif text == "➕ Anime qo'shish":
            msg = bot.send_message(user_id, "✏️ Yangi anime kodini kiriting:")
            bot.register_next_step_handler(msg, process_anime_kod)
        elif text == "📂 Anime ro'yxati":
            show_anime_list(user_id)
        elif text == "➕ Qism qo'shish":
            msg = bot.send_message(user_id, "✏️ Qism qo'shmoqchi bo'lgan anime kodini kiriting:")
            bot.register_next_step_handler(msg, process_qism_anime_kod)
        elif text == "📤 Kanal post":
            msg = bot.send_message(user_id, "✏️ Kanalga yuboriladigan anime kodini kiriting:")
            bot.register_next_step_handler(msg, process_kanal_post_kod)
        elif text == "🎬 Anime qidirish":
            bot.send_message(user_id, "🔍 Anime kodini yozib yuboring:")
        elif text == "🏧 Admin bilan aloqa":
            bot.send_message(user_id, "Bu tugma foydalanuvchilar uchun mo'ljallangan.")
        else:
            show_anime_to_admin(user_id, text)
    else:
        if text == "🎬 Anime qidirish":
            bot.send_message(user_id, "🔍 Anime kodini yozib yuboring:")
        elif text == "🏧 Admin bilan aloqa":
            msg = bot.send_message(user_id, "✍️ Muammo yoki taklifingizni yozib yuboring, men adminga yetkazaman:")
            bot.register_next_step_handler(msg, forward_to_admin)
        else:
            show_anime_to_user(user_id, text)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 **Yangi xabar!**\nKimdan: {message.from_user.first_name} (ID: {message.chat.id})\n\nXabar: {message.text}")
    bot.send_message(message.chat.id, "✅ Xabaringiz adminga yuborildi!")

def process_anime_kod(message):
    anime_kod = message.text
    msg = bot.send_message(message.chat.id, "🎬 Anime nomini kiriting:")
    bot.register_next_step_handler(msg, process_anime_nomi, anime_kod)

def process_anime_nomi(message, anime_kod):
    anime_nomi = message.text
    msg = bot.send_message(message.chat.id, "🏞 Anime rasmini yuboring (Rasm ko'rinishida):")
    bot.register_next_step_handler(msg, process_anime_rasm, anime_kod, anime_nomi)

def process_anime_rasm(message, anime_kod, anime_nomi):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Bu rasm emas. Qayta urinib ko'ring.")
        return
    rasm_id = message.photo[-1].file_id
    tavsif = f"🎬 **Anime nomi:** {anime_nomi}\n🎞 **Qismlar soni:** 12\n📅 **Yil:** {datetime.now().year}\n#️⃣ **Kod:** {anime_kod}"
    
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO animes (kod, nomi, rasm, tavsif) VALUES (?, ?, ?, ?)", 
                   (anime_kod, anime_nomi, rasm_id, tavsif))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Anime muvaffaqiyatli qo'shildi!\nKod: {anime_kod}")

def show_anime_list(user_id):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT kod, nomi, rasm FROM animes")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        bot.send_message(user_id, "🗂 Ro'yxat bo'sh.")
        return
    for row in rows:
        bot.send_photo(user_id, row[2], caption=f"🎬 {row[1]}\n#️⃣ Kod: {row[0]}", reply_markup=inline_boshqaruv_baneri(row[0]))

def process_qism_anime_kod(message):
    anime_kod = message.text
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nomi FROM animes WHERE kod=?", (anime_kod,))
    anime = cursor.fetchone()
    if not anime:
        bot.send_message(message.chat.id, SOZ_TOPILMADI)
        conn.close()
        return
    cursor.execute("SELECT MAX(qism_raqam) FROM qismlar WHERE anime_kod=?", (anime_kod,))
    max_qism = cursor.fetchone()[0]
    keyingi_qism = (max_qism if max_qism else 0) + 1
    conn.close()
    msg = bot.send_message(message.chat.id, f"🎬 {anime[0]} uchun **{keyingi_qism}-qism** videosini yuboring:")
    bot.register_next_step_handler(msg, save_anime_qism, anime_kod, keyingi_qism)

def save_anime_qism(message, anime_kod, qism_raqam):
    if message.content_type != 'video':
        bot.send_message(message.chat.id, "❌ Iltimos, video fayl yuboring!")
        return
    video_id = message.video.file_id
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO qismlar (anime_kod, qism_raqam, video_id) VALUES (?, ?, ?)", 
                   (anime_kod, qism_raqam, video_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ {qism_raqam}-qism muvaffaqiyatli saqlandi!")

def process_kanal_post_kod(message):
    anime_kod = message.text
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nomi, rasm, tavsif FROM animes WHERE kod=?", (anime_kod,))
    anime = cursor.fetchone()
    conn.close()
    if not anime:
        bot.send_message(message.chat.id, SOZ_TOPILMADI)
        return
    bot_info = bot.get_me()
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("🔹 Tomosha qilish 🔹", url=f"https://t.me/{bot_info.username}?start={anime_kod}"))
    bot.send_photo(KANAL_USERNAME, anime[1], caption=anime[2], reply_markup=inline_markup)
    bot.send_message(message.chat.id, "✅ Post kanalga muvaffaqiyatli yuborildi!")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    data = call.data.split('_')
    action = data[0]
    
    if action == "view" and data[1] == "qismlar":
        show_qismlar_to_user(call.message.chat.id, data[2])
    elif action == "edit" and data[1] == "name":
        msg = bot.send_message(call.message.chat.id, f"📝 {data[2]} uchun yangi nom kiriting:")
        bot.register_next_step_handler(msg, update_anime_name, data[2])
    elif action == "edit" and data[1] == "desc":
        msg = bot.send_message(call.message.chat.id, f"📝 {data[2]} uchun yangi to'liq tavsif yozing:")
        bot.register_next_step_handler(msg, update_anime_desc, data[2])
    elif action == "edit" and data[1] == "pic":
        msg = bot.send_message(call.message.chat.id, f"📝 {data[2]} uchun yangi rasm yuboring:")
        bot.register_next_step_handler(msg, update_anime_pic, data[2])
    elif action == "delete":
        conn = sqlite3.connect('anime_bot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM animes WHERE kod=?", (data[1],))
        cursor.execute("DELETE FROM qismlar WHERE anime_kod=?", (data[1],))
        conn.commit()
        conn.close()
        bot.edit_message_caption("🗑 Anime o'chirildi!", call.message.chat.id, call.message.message_id)
    elif action == "back" and data[1] == "to":
        bot.send_message(call.message.chat.id, "Bosh menyuga qaytildi.", reply_markup=admin_menu())
    elif action == "play":
        conn = sqlite3.connect('anime_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT video_id, qism_raqam FROM qismlar WHERE id=?", (data[1],))
        res = cursor.fetchone()
        conn.close()
        if res:
            bot.send_video(call.message.chat.id, res[0], caption=f"🎬 {res[1]}-qism")

def update_anime_name(message, anime_kod):
    new_name = message.text
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE animes SET nomi=? WHERE kod=?", (new_name, anime_kod))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Anime nomi o'zgartirildi!")

def update_anime_pic(message, anime_kod):
    if message.content_type != 'photo': return
    rasm_id = message.photo[-1].file_id
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE animes SET rasm=? WHERE kod=?", (rasm_id, anime_kod))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Rasm o'zgartirildi!")

def update_anime_desc(message, anime_kod):
    new_desc = message.text
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE animes SET tavsif=? WHERE kod=?", (new_desc, anime_kod))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Tavsif o'zgartirildi!")

def show_anime_to_admin(user_id, anime_kod):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nomi, rasm, tavsif FROM animes WHERE kod=?", (anime_kod,))
    anime = cursor.fetchone()
    conn.close()
    if anime:
        bot.send_photo(user_id, anime[1], caption=anime[2], reply_markup=inline_boshqaruv_baneri(anime_kod))
    else:
        bot.send_message(user_id, SOZ_TOPILMADI)

def show_anime_to_user(user_id, anime_kod):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nomi, rasm, tavsif FROM animes WHERE kod=?", (anime_kod,))
    anime = cursor.fetchone()
    conn.close()
    if anime:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🍿 Qismlarni tomosha qilish", callback_data=f"view_qismlar_{anime_kod}"))
        bot.send_photo(user_id, anime[1], caption=anime[2], reply_markup=markup)
    else:
        bot.send_message(user_id, SOZ_TOPILMADI)

def show_qismlar_to_user(user_id, anime_kod):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, qism_raqam FROM qismlar WHERE anime_kod=? ORDER BY qism_raqam ASC", (anime_kod,))
    qismlar = cursor.fetchall()
    conn.close()
    if not qismlar:
        bot.send_message(user_id, "⚠️ Qismlar hali yuklanmagan.")
        return
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(f"{q[1]}-qism", callback_data=f"play_{q[0]}") for q in qismlar]
    markup.add(*buttons)
    bot.send_message(user_id, "🍿 Qismni tanlang:", reply_markup=markup)

def show_statistics(user_id):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    bugun = datetime.now().strftime("%Y-%m-%d")
    hafta = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    oy = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date=?", (bugun,))
    users_today = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date>=?", (hafta,))
    users_week = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date>=?", (oy,))
    users_month = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM qismlar")
    total_qismlar = cursor.fetchone()[0]
    conn.close()
    
    stat_text = (
        f"📊 **Bot Statistikasi:**\n\n"
        f"👤 Jami obunachilar: {total_users} ta\n"
        f"📅 Bugun qo'shilganlar: {users_today} ta\n"
        f"📆 Oxirgi 7 kunda: {users_week} ta\n"
        f"📅 Oxirgi 30 kunda: {users_month} ta\n\n"
        f"🎬 Jami yuklangan anime qismlari: {total_qismlar} ta\n"
        f"📆 Sana: {datetime.now().strftime('%Y.%m.%d')}"
    )
    bot.send_message(user_id, stat_text)

if __name__ == '__main__':
    import time
    while True:
        try:
            print("Bot 24/7 rejimida ishga tushdi...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Xatolik yuz berdi: {e}. Qayta ulanmoqda...")
            time.sleep(5)
