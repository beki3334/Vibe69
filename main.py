
import os
import logging
import yt_dlp
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from flask import Flask
import threading

API_TOKEN = os.getenv("API_TOKEN")  # Токен из секретов Replit

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- Flask сервер для UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask).start()


# --- Команда /start ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("🎧 Привет! Напиши название песни или исполнителя — я найду и пришлю тебе аудио.")


# --- Обработка текста (поиск и отправка музыки) ---
@dp.message_handler()
async def send_song(message: types.Message):
    query = message.text

    await message.reply("🔎 Ищу песню, подожди...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': 'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            audio_file = ydl.prepare_filename(info['entries'][0]).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            title = info['entries'][0]['title']
            artist = info['entries'][0]['uploader']

        with open(audio_file, 'rb') as audio:
            await bot.send_audio(message.chat.id, audio, title=title, performer=artist)

        os.remove(audio_file)

    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")


# --- Запуск бота ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
