import json
import logging
import sys
import asyncio
from aiogram import Bot, Dispatcher, Router, F, enums
from aiogram.filters import Command
from aiogram.types import Message
from handlers import questions, yt_handler

dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет")
    
@router.message(F.text)
async def message_with_text(message: Message):
    if yt_handler.yt.open_youtube_link(message.text):
        await message.answer("Это ссылка на видео! /download ?")
    else:
        await message.answer("Это текст!")

@router.message(F.sticker)
async def message_with_sticker(message: Message):
    await message.answer("Это стикер!")

@router.message(F.animation)
async def message_with_gif(message: Message):
    await message.answer("Это GIF!")

def get_token():
    # Загрузка данных из JSON файла
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            API_TOKEN = config.get("API_TOKEN")
            return API_TOKEN
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка при загрузке API_TOKEN из файла: {str(e)}")
        exit(1)

async def main() -> None:
    try:
        bot = Bot(get_token())
        dp.include_routers(questions.router, yt_handler.router, router)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка при инициализации бота: {str(e)}")
        exit(1)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
