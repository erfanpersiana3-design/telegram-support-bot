import os
import asyncio
import sqlite3
import time
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5133448276  # ← اینجا chat_id گروهتو بزار

bot = Bot(token=TOKEN)
dp = Dispatcher()

# دیتابیس
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TEXT,
    message_count INTEGER DEFAULT 0,
    blocked INTEGER DEFAULT 0,
    last_message_time INTEGER DEFAULT 0
)
""")

conn.commit()

# تولید کد پیگیری
def generate_ticket():
    return f"T{random.randint(1000,9999)}"

# پیام استارت
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "سلام 👋\n"
        "برای ارسال پیام، فقط متن یا فایل خود را ارسال کنید.\n"
        "پشتیبانی در سریع‌ترین زمان پاسخ می‌دهد."
    )

# دریافت پیام کاربر
@dp.message(F.chat.type == "private")
async def handle_user_message(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username or "ندارد"
    full_name = message.from_user.full_name
    now = int(time.time())

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user:
        if user[4] == 1:
            return
        if now - user[5] < 30:
            await message.answer("لطفاً کمی صبر کنید ⏳")
            return
        cursor.execute("""
            UPDATE users
            SET message_count = message_count + 1,
                last_message_time = ?
            WHERE user_id=?
        """, (now, user_id))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, username, first_seen, message_count, blocked, last_message_time)
            VALUES (?, ?, datetime('now'), 1, 0, ?)
        """, (user_id, username, now))

    conn.commit()

    ticket = generate_ticket()

    caption = (
        f"📩 پیام جدید\n\n"
        f"👤 نام: {full_name}\n"
        f"🆔 آیدی: {user_id}\n"
        f"🔗 یوزرنیم: @{username}\n"
        f"🎟 کد پیگیری: #{ticket}\n\n"
    )

    if message.text:
        await bot.send_message(GROUP_ID, caption + message.text)
    elif message.photo:
        await bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption)
    elif message.video:
        await bot.send_video(GROUP_ID, message.video.file_id, caption=caption)
    elif message.voice:
        await bot.send_voice(GROUP_ID, message.voice.file_id, caption=caption)
    elif message.document:
        await bot.send_document(GROUP_ID, message.document.file_id, caption=caption)

    await message.answer(f"پیام شما ارسال شد ✅\nکد پیگیری: #{ticket}")

# پاسخ از گروه
@dp.message(F.chat.id == GROUP_ID)
async def handle_group_reply(message: Message):
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if text and "🆔 آیدی:" in text:
            user_id = int(text.split("🆔 آیدی: ")[1].split("\n")[0])
            await bot.send_message(user_id, message.text + "\n\nپشتیبانی")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
