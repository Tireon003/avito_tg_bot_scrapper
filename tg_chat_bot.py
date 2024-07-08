import asyncio
import logging
import json
import base64
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from collections import defaultdict
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

# Условное хранилище таблицы

table = defaultdict()

# конец хранилища


@dp.message(Command("table"))
async def show_table(message: types.Message):
    await message.answer(str(table.keys()))


class AddToTableCallbackFactory(CallbackData, prefix='addtotable_fab'):
    action: str
    value: str


@dp.message(F.text)
async def parse_url(message: types.Message):
    new_driver_manager = WebDriverManager()
    try:
        parsed_page = PageDataParser(message.text, new_driver_manager.init_webdriver())
        parsed_data = parsed_page()
        print(type(parsed_data))
        parsed_data_json = json.dumps(parsed_data)
        parsed_data_base64 = base64.b64encode(parsed_data_json.encode()).decode()
        print(type(parsed_data_base64))
        builder = InlineKeyboardBuilder()
        if parsed_data["ID"] not in table.keys():
            print("принт перед созданием кнопки")
            builder.button(
                text="Добавить объявление в таблицу",
                callback_data=AddToTableCallbackFactory(action="add", value=parsed_data_base64)  # todo решить проблему с ограничением 64 байт или сразу реализовыввать БД
            )
            print("not in прошел")
        else:
            print("принт перед созданием кнопки")
            builder.button(
                text="Удалить объявление из таблицы",
                callback_data=AddToTableCallbackFactory(action="pop", value=parsed_data_base64)
            )
            print("else прошел")
        text_answer = ""
        print("до for проходит")
        for key, value in parsed_data.items():
            print("начало for")
            text_answer += f'{key}: {value}\n'
            print('конец блока for прршел')
        await message.reply(text_answer, reply_markup=builder.as_markup())
        print("await прошел")
    except ValueError as ve:
        print(ve)  # Служебное сообщение, удалить после фикса бага
        await message.reply("Введена некорректная ссылка на объявление!")
    except NoSuchElementException:
        await message.reply("Не удалось загрузить страницу с объявлением. Повторите попытку позже...")
    finally:
        new_driver_manager.close_webdriver()


@dp.callback_query(AddToTableCallbackFactory.filter())
async def put_product_into_table(callback: types.CallbackQuery, callback_data: AddToTableCallbackFactory):
    page_data_json = base64.b64decode(callback_data['value']).decode()
    page_data = json.loads(page_data_json)
    if callback_data.action == "add":
        table[page_data["ID"]] = page_data
        await callback.message.answer(f"Объявление с id: {page_data["ID"]} добавлено в таблицу.")
    elif callback_data.action == "pop":
        del table[page_data["ID"]]
        await callback.message.answer(f"Объявление с id: {page_data["ID"]} удалено из таблицы.")
    else:
        await callback.message.answer(f'Произошла ошибка, повторите снова!')


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
