import json, logging, sys, asyncio
from aiogram import Bot, Dispatcher
import handlers

dp = Dispatcher()

try:
    with open("configs/bot.json", "r") as config_file:
        config = json.load(config_file)
    bot = Bot(config.get("API_TOKEN"))
except Exception as e:
    logging.critical(f"Ошибка при инициализации бота: {str(e)}")
    exit(1)

async def startup():
    logging.debug("Вывод сообщения о запуске")
    try:
        await bot.send_message(chat_id=config.get("ADMIN_ID"), text='Бот запущен')
    except Exception as e:
        logging.error(f"Ошибка отправки startup сообщения: {str(e)}")


async def main() -> None:
    try:
        dp.include_routers(handlers.yt_loader_handler.router, handlers.default_commands_handler.router)
        dp.startup.register(startup)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Ошибка при запуске бота: {str(e)}")
        exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
