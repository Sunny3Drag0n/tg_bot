import json
import logging
import sys
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
import handlers

dp = Dispatcher()
router = Router()

try:
    with open("configs/bot.json", "r") as config_file:
        config = json.load(config_file)
    bot = Bot(config.get("API_TOKEN"))
except Exception as e:
    logging.critical(f"Ошибка при инициализации бота: {str(e)}")
    exit(1)


@router.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"chat_id={message.chat.id}, first_name={message.from_user.first_name}, last_name={message.from_user.last_name}, username={message.from_user.username}")
    text=f'Привет {message.from_user.username}'
    # регистрация?
    await message.answer(text)

@router.message(Command("me"))
async def cmd_start(message: Message):
    await message.answer(f"chat_id:     {message.chat.id}\n" + 
                         f"first_name:  {message.from_user.first_name}\n" +
                         f"last_name:   {message.from_user.last_name}\n" +
                         f"username:    {message.from_user.username}")

@router.message(Command("clear"))
async def cmd_start(message: Message):
    pass

async def startup():
    logging.debug("Вывод сообщения о запуске")
    try:
        await bot.send_message(chat_id=config.get("ADMIN_ID"), text='Бот запущен')
    except Exception as e:
        logging.error(f"Ошибка отправки startup сообщения: {str(e)}")


async def main() -> None:
    try:
        dp.include_routers(handlers.yt_handler.router, router)
        dp.startup.register(startup)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Ошибка при запуске бота: {str(e)}")
        exit(1)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
