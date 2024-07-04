import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from bot_config import config
import scrapper as sc

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.bot_token.get_secret_value())
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Scrap from Avito.ru!")


# todo Добавить кнопку под ответным сообщением (см. Идеи проекта ТГ)
@dp.message(F.text)
async def parse_url(message: types.Message):
    try:
        parsed_page = sc.PageDataParser(message.text, sc.my_driver)
        text_answer = ""
        for key, value in parsed_page().items():
            text_answer += f'{key}: {value}\n'
        await message.reply(text_answer)
    except ValueError:
        await message.reply("Введена некорректная ссылка на объявление!")

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
