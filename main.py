import asyncio
import logging
from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher
from handlers import url_parser, main_handler, category_parser


async def main():
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_routers(category_parser.router, main_handler.router, url_parser.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
