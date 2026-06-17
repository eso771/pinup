import sqlite3
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- AYARLAR ---
API_ID = 10079905          # Öz API ID-nizi yazın
API_HASH = "e4a5fa251e2e055f26e5c2add8401530"  # Öz API Hash-inizi yazın
BOT_TOKEN = "8805123493:AAHETZ2RphaMdPrKwwWKPnAK8S2YZx9ke1Q" # Öz Bot Tokeninizi yazın
ADMIN_ID = 8300963721      # Bot sahibinin (Sizin) Telegram ID-niz
IMAGE_URL = "IMG_20260617_175753_868.jpg"  # Start mesajlarında görünəcək şəkil linki

bot = Client("pinup_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- VERİLƏNLƏR BAZASI (SQLite) ---
def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_verified INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def is_user_verified(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_verified FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0] == 1

def verify_user(user_id):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, is_verified) VALUES (?, 1)", (user_id,))
    conn.commit()
    conn.close()

# İstifadəçi vəziyyətlərini yadda saxlamaq üçün müvəqqəti lüğət (dict)
# Məsələn: {user_id: "waiting_deposit"} və ya {user_id: "waiting_withdraw"}
user_states = {}

# --- BUTTONLAR ---
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Depozit etmək", callback_data="deposit"),
         InlineKeyboardButton("💳 Çıxarış etmək", callback_data="withdraw")],
        [InlineKeyboardButton("👨🏻‍💻 Menecerlə əlaqə", callback_data="manager")]
    ])

# --- COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    bot_info = await client.get_me()
    bot_mention = bot_info.mention
    
    # Əgər istifadəçi artıq təsdiqlənibsə
    if is_user_verified(user_id):
        text = (
            "PIN-UP Premium Bot -a xoş gəldin 👋🏻\n"
            "Aşağıdakı buttonlardan istifadə edərək bizimlə əlaqəyə keçə bilərsən ✋🏻"
        )
        await message.reply_photo(
            photo=IMAGE_URL,
            caption=text,
            reply_markup=main_menu_keyboard()
        )
    else:
        # İlk dəfə gələn istifadəçi
        text = (
            f"Salam 👋🏻\n"
            f"{bot_mention} -a xoş gəldin 🤩\n"
            f"Bu bot ilə müəyyən əməliyyat növləri keçirə bilərsən ✋🏻\n\n"
            f"Bonus, kassa əməliyyatları və digər çox növlü əməliyyatlar üçün ✅ **Giriş et** buttona kliklə 🎁"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Giriş et", callback_data="login")],
            [InlineKeyboardButton("🌐 Sayt", url="https://example.com")] # Sayt linkini bura yazın
        ])
        await message.reply_photo(
            photo=IMAGE_URL,
            caption=text,
            reply_markup=keyboard
        )

# --- CALLBACK HANDLERS (Button kliklənmələri) ---
@bot.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "login":
        text = (
            "PIN-UP Premium Bot-ə abunəni aktivləşdirmək üçün avtorizasiya et 😉\n\n"
            "🚀 Sayta keç və ID nömrən ilə qeydiyyat nömrəsini kopyalayıb bota göndər"
        )
        user_states[user_id] = "waiting_auth_id"
        # Şəkilli mesajın mətnini editləyirik
        await callback_query.message.edit_caption(caption=text)
        
    elif data == "deposit":
        text = "✍🏻 Depozit etmək istədiyiniz məbləği yazın."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geriyə qayıtmaq", callback_data="back_to_menu")]])
        user_states[user_id] = "waiting_deposit_amount"
        await callback_query.message.edit_caption(caption=text, reply_markup=keyboard)

    elif data == "withdraw":
        text = "✍🏻 Çıxarış edəcəyiniz məbləği qeyd edin."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geriyə qayıtmaq", callback_data="back_to_menu")]])
        user_states[user_id] = "waiting_withdraw_amount"
        await callback_query.message.edit_caption(caption=text, reply_markup=keyboard)

    elif data == "manager":
        text = (
            "🎁 PIN-UP Premium Bot - vasitəsilə köməkçi menecer-ə qoşulursunuz \n\n"
            "👨🏻‍💻 Bir qədər gözləyin, menecer sizə geri dönüş edəcək."
        )
        await callback_query.message.edit_caption(caption=text, reply_markup=main_menu_keyboard())
        
        # Adminə bildiriş göndərilməsi
        username = f"@{callback_query.from_user.username}" if callback_query.from_user.username else "Yoxdur"
        user_mention = callback_query.from_user.mention
        
        admin_text = (
            "🔔 Menecer-ə əlaqə məktubu:\n"
            f"👤: {username}\n"
            f"✍🏻: {user_mention}"
        )
        try:
            await client.send_message(chat_id=ADMIN_ID, text=admin_text)
        except Exception as e:
            print(f"Adminə mesaj göndərilə bilmədi: {e}")

    elif data == "back_to_menu":
        # Vəziyyəti sıfırlayırıq və menyuya qayıdırıq
        user_states.pop(user_id, None)
        text = (
            "PIN-UP Premium Bot - tərəfindən təsdiqlənmə uğurla başa çatdı 🤩\n\n"
            "🚀 Əməliyyatlar üçün buttonlardan istifadə et"
        )
        await callback_query.message.edit_caption(caption=text, reply_markup=main_menu_keyboard())

# --- TEXT MESSAGES HANDLER (Mətn daxil edilməsi) ---
@bot.on_message(filters.text & filters.private)
async def text_handler(client, message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    username = f"@{message.from_user.username}" if message.from_user.username else "Yoxdur"
    user_mention = message.from_user.mention

    if state == "waiting_auth_id":
        # İstifadəçi ID göndərdi -> Təsdiqləyirik
        verify_user(user_id)
        user_states.pop(user_id, None) # Vəziyyəti təmizləyirik
        
        # Botun köhnə (şəkilli) mesajını silmək funksiyası yoxdur, 
        # amma məntiqə görə yeni şəkil göndərib köhnəni silə bilərik.
        # Sadəlik üçün əvvəlki mesajı silmək əvəzinə, yeni təmiz mesaj göndəririk.
        
        text = (
            "PIN-UP Premium Bot - tərəfindən təsdiqlənmə uğurla başa çatdı 🤩\n\n"
            "🚀 Əməliyyatlar üçün buttonlardan istifadə et"
        )
        await message.reply_photo(
            photo=IMAGE_URL,
            caption=text,
            reply_markup=main_menu_keyboard()
        )

    elif state == "waiting_deposit_amount":
        amount = message.text
        user_states.pop(user_id, None)
        
        await message.reply_text("PIN-UP Premium Bot - tərəfindən depozit məbləğiniz təsdiqləndi ✅\n\n🚀 Bot tərəfindən Menecer-ə yönəldilirsiniz")
        
        # Adminə bildiriş
        admin_text = (
            "🔔 Depozit məktubu:\n"
            f"👤: {username}\n"
            f"✍🏻: {user_mention}\n"
            f"💸: {amount}"
        )
        await client.send_message(chat_id=ADMIN_ID, text=admin_text)

    elif state == "waiting_withdraw_amount":
        amount = message.text
        user_states.pop(user_id, None)
        
        await message.reply_text("PIN-UP Premium Bot - tərəfindən çıxarış məbləğiniz təsdiqləndi ✅\n\n🚀 Bot tərəfindən Menecer-ə yönəldilirsiniz")
        
        # Adminə bildiriş
        admin_text = (
            "🔔 Çıxarış məktubu:\n"
            f"👤: {username}\n"
            f"✍🏻: {user_mention}\n"
            f"💸: {amount}"
        )
        await client.send_message(chat_id=ADMIN_ID, text=admin_text)

if __name__ == "__main__":
    init_db()  # Bazanı yaradırıq
    print("Bot başladıldı...")
    bot.run()
  
