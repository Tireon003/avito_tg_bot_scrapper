import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
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
        await db.add_user(message.from_user.id)
        await message.answer("Scrap from Avito.ru!")


@dp.message(Command("table"))
async def show_table(message: types.Message):
    async with Database() as db:
        user_data = await db.get_user_data(message.from_user.id)
        await message.answer(user_data)


@dp.message(Command("clear"))
async def show_table(message: types.Message):
    async with Database() as db:
        await db.update_user_data(message.from_user.id, '{}')
        await message.reply("Таблица очищена!")


# todo Разобраться где хранить фабрики коллбеков
class AddToTableCallbackFactory(CallbackData, prefix='addtotable_fab'):
    action: str
    value: int
    user_id: int


@dp.message(F.text)
async def parse_url(message: types.Message):
    async with Database() as db:
        new_driver_manager = WebDriverManager()
        try:
            parsed_page = PageDataParser(message.text, new_driver_manager.init_webdriver())
            parsed_data = parsed_page()
            parsed_data_json = json.dumps(parsed_data)
            await db.put_product_to_history(parsed_data["ID"], parsed_data_json)
            user_data_from_db = await db.get_user_data(message.from_user.id)
            current_user_id_list = json.loads(user_data_from_db).keys()
            builder = InlineKeyboardBuilder()
            if parsed_data["ID"] not in current_user_id_list:
                builder.button(
                    text="Добавить объявление в таблицу",
                    callback_data=AddToTableCallbackFactory(
                        action="add",
                        value=parsed_data["ID"],
                        user_id=message.from_user.id
                    )
                )
            else:
                builder.button(
                    text="Удалить объявление из таблицы",
                    callback_data=AddToTableCallbackFactory(
                        action="pop",
                        value=parsed_data["ID"],
                        user_id=message.from_user.id
                    )
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


# todo Добавить изменение настроек inline-кнопки сообщения в зависимости от action.
# todo Вынести InlineKeyboardBuilder в отдельную функцию
# todo Вынести преобразование данных в json и обратно в отдельный класс
# todo Декомпозировать код
@dp.callback_query(AddToTableCallbackFactory.filter())
async def put_product_into_table(callback: types.CallbackQuery, callback_data: AddToTableCallbackFactory):
    async with Database() as db:
        product_id = callback_data.value
        user_id = callback_data.user_id
        current_product_info = await db.get_product_from_history(product_id)
        page_data = json.loads(current_product_info[1])
        user_data_from_db = await db.get_user_data(user_id)
        current_user_data = json.loads(user_data_from_db)
        if callback_data.action == "add":
            current_user_data[product_id] = page_data
            current_user_data_json = json.dumps(current_user_data)
            await db.update_user_data(user_id, current_user_data_json)
            await callback.message.answer(f"Объявление с id: {product_id} добавлено в таблицу.")
        elif callback_data.action == "pop":
            del current_user_data[product_id]
            current_user_data_json = json.dumps(current_user_data)
            await db.update_user_data(user_id, current_user_data_json)
            await callback.message.answer(f"Объявление с id: {product_id} удалено из таблицы.")
        else:
            await callback.message.answer(f'Произошла ошибка, повторите снова!')


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
