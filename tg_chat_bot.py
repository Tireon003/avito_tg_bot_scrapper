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
from modules.scrapper.scrapper import WebDriverManager, PageDataParser
from modules.database.database import Database
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
    async with Database() as db:
        db.add_user(message.from_user.id)
        await message.answer("Scrap from Avito.ru!")

# Условное хранилище таблицы

table = defaultdict()

# конец хранилища


@dp.message(Command("table"))
async def show_table(message: types.Message):
    async with Database() as db:
        user_data = await db.get_user_data(message.from_user.id)
        await message.answer(user_data)


class AddToTableCallbackFactory(CallbackData, prefix='addtotable_fab'):
    action: str
    value: int


@dp.message(F.text)
async def parse_url(message: types.Message):
    async with Database() as db:
        new_driver_manager = WebDriverManager()
        try:
            parsed_page = PageDataParser(message.text, new_driver_manager.init_webdriver())
            parsed_data = parsed_page()
            parsed_data_json = json.dumps(parsed_data)
            parsed_data_base64 = base64.b64encode(parsed_data_json.encode()).decode()
            table[parsed_data["ID"]] = parsed_data_base64
            current_user_id_list = json.loads(await db.get_user_data(message.from_user.id)).keys()
            builder = InlineKeyboardBuilder()
            if parsed_data["ID"] not in current_user_id_list:
                builder.button(
                    text="Добавить объявление в таблицу",
                    callback_data=AddToTableCallbackFactory(action="add", value=parsed_data["ID"])
                )
            else:
                builder.button(
                    text="Удалить объявление из таблицы",
                    callback_data=AddToTableCallbackFactory(action="pop", value=parsed_data["ID"])
                )
            text_answer = ""
            for key, value in parsed_data.items():
                text_answer += f'{key}: {value}\n'
            await message.reply(text_answer, reply_markup=builder.as_markup())
        except ValueError:
            await message.reply("Введена некорректная ссылка на объявление!")
        except NoSuchElementException:
            await message.reply("Не удалось загрузить страницу с объявлением. Повторите попытку позже...")
        finally:
            new_driver_manager.close_webdriver()


@dp.callback_query(AddToTableCallbackFactory.filter())
async def put_product_into_table(callback: types.CallbackQuery, callback_data: AddToTableCallbackFactory):
    async with Database() as db:
        product_id = callback_data.value
        page_data_json = base64.b64decode(table[product_id]).decode()
        page_data = json.loads(page_data_json)
        current_user_data = json.loads(await db.get_user_data(callback.message.from_user.id))
        print(current_user_data, type(current_user_data), "принт в коллбэке")
        if callback_data.action == "add":
            current_user_data[product_id] = page_data
            await db.update_user_data(callback.message.from_user.id, current_user_data)
            await callback.message.answer(f"Объявление с id: {page_data['ID']} добавлено в таблицу.")
        elif callback_data.action == "pop":
            del current_user_data[product_id]
            await db.update_user_data(callback.message.from_user.id, current_user_data)
            await callback.message.answer(f"Объявление с id: {page_data['ID']} удалено из таблицы.")
        else:
            await callback.message.answer(f'Произошла ошибка, повторите снова!')


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
