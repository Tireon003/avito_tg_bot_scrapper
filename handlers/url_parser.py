import json

from aiogram.types import ReplyKeyboardRemove

from factories.add_to_table_fab import AddToTableCallbackFactory
from keyboards.product_inline_keyboard import action_with_product_inline
from modules.scrapper.scrapper import WebDriverManager, PageDataParser
from selenium.common import NoSuchElementException
from modules.database.database import Database
from aiogram import types, F, Router

router = Router()


@router.message(F.text)
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
            text_answer = ""
            if parsed_data["ID"] not in current_user_id_list:
                action_tag = "add"
            else:
                action_tag = "pop"
            for key, value in parsed_data.items():
                text_answer += f'{key}: {value}\n'
            await message.reply(
                text=text_answer,
                reply_markup=action_with_product_inline(action_tag, parsed_data["ID"], message.from_user.id)
            )
        except ValueError:
            await message.reply(
                text="Введена некорректная ссылка на объявление!",
                reply_markup=ReplyKeyboardRemove()
            )
        except NoSuchElementException:
            await message.reply(
                text="Не удалось загрузить страницу с объявлением. Повторите попытку позже...",
                reply_markup=ReplyKeyboardRemove()
            )
        finally:
            new_driver_manager.close_webdriver()


@router.callback_query(AddToTableCallbackFactory.filter())
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
