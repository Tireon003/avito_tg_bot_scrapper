import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from bot_config import config
from scrapper import WebDriverManager, PageDataParser
from selenium.common import NoSuchElementException

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
    new_driver_manager = WebDriverManager()
    try:
        parsed_page = PageDataParser(message.text, new_driver_manager.init_webdriver())
        text_answer = ""
        for key, value in parsed_page().items():
            text_answer += f'{key}: {value}\n'
        await message.reply(text_answer)
    except ValueError:
        await message.reply("Введена некорректная ссылка на объявление!")
    except NoSuchElementException:
        await message.reply("Не удалось загрузить страницу с объявлением. Повторите попытку позже...")
    new_driver_manager.close_webdriver()

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
