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

try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    bot = Bot(config.get("API_TOKEN"))
except Exception as e:
    logging.CRITICAL(f"Ошибка при инициализации бота: {str(e)}")
    exit(1)

@router.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"chat_id={message.chat.id}, first_name={message.from_user.first_name}, last_name={message.from_user.last_name}, username={message.from_user.username}")
    await message.answer(f"Привет {message.from_user.username}")

@router.message(Command("me"))
async def cmd_start(message: Message):
    await message.answer(f"chat_id:     {message.chat.id}\n" + 
                         f"first_name:  {message.from_user.first_name}\n" +
                         f"last_name:   {message.from_user.last_name}\n" +
                         f"username:    {message.from_user.username}")
    
@router.message(F.text)
async def message_with_text(message: Message):
    await message.answer("Это текст!")

@router.message(F.sticker)
async def message_with_sticker(message: Message):
    await message.answer("Это стикер!")

@router.message(F.animation)
async def message_with_gif(message: Message):
    await message.answer("Это GIF!")

async def startup():
    logging.debug("Вывод сообщения о запуске")
    try:
        await bot.send_message(chat_id=config.get("ADMIN_ID"), text='Бот запущен')
    except Exception as e:
        logging.error(f"Ошибка отправки startup сообщения: {str(e)}")



async def main() -> None:
    try:
        dp.include_routers(questions.router, yt_handler.router, router)
        dp.startup.register(startup)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Ошибка при запуске бота: {str(e)}")
        exit(1)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
