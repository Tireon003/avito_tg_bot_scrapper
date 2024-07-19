import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot_config import config
from handlers import url_parser, main_handler, category_parser


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    dp.include_routers(category_parser.router, main_handler.router, url_parser.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
