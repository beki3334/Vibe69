import os
import logging
import yt_dlp
import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from flask import Flask
import threading

API_TOKEN = os.getenv("API_TOKEN")  # Токен из секретов Replit

if not API_TOKEN:
    raise ValueError("API_TOKEN не найден в переменных окружения")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Flask сервер для UptimeRobot ---
app = Flask('')


@app.route('/')
def home():
    return "Bot is alive!"


def run_flask():
    app.run(host='0.0.0.0', port=8080)


threading.Thread(target=run_flask).start()


# --- Команда /start ---
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply(
        "🎧 Привет! Напиши название песни или исполнителя — я найду и пришлю тебе аудио."
    )


# --- Обработка текста (поиск и отправка музыки) ---
@dp.message()
async def send_song(message: types.Message):
    query = message.text

    await message.reply("🔎 Ищу песню, подожди...")

    ydl_opts = {
        'format':
        'bestaudio/best',
        'noplaylist':
        True,
        'quiet':
        True,
        'outtmpl':
        'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            if not info or 'entries' not in info or not info['entries']:
                raise Exception("Песня не найдена")
            
            entry = info['entries'][0]
            audio_file = ydl.prepare_filename(entry).replace(
                '.webm', '.mp3').replace('.m4a', '.mp3')
            title = entry.get('title', 'Неизвестное название')
            artist = entry.get('uploader', 'Неизвестный исполнитель')

        audio_input = FSInputFile(audio_file)
        await bot.send_audio(message.chat.id,
                             audio_input,
                             title=title,
                             performer=artist)

        os.remove(audio_file)

    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")


# --- Запуск бота ---
async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
