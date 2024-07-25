from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.handlers import router
from database.models import async_main as database_main
from database.requests import main as requests_main

import asyncio
import os


load_dotenv()


async def main():
    await database_main()
    await requests_main()
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dispatcher = Dispatcher()
    dispatcher.include_router(router=router)
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен.')