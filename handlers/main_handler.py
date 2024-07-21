import json
from aiogram import types, Router
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from factories.save_table_to_csv_fab import SaveTableToFileCSV
from keyboards.save_table_to_file_keyboard import action_table_to_csv
from modules.database.database import Database
from modules.table_manager import Table

router: Router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    async with Database() as db:
        await db.add_user(message.from_user.id)
    await message.answer(
        text="Добро пожаловать! Бот предназначен для парсинга данных из объявлений на Авито по ссылке, " +
        "либо же парсинга объявлений конкретной категории.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("table"))
async def show_table(message: types.Message):
    async with Database() as db:
        user_products_json = await db.get_user_data(message.from_user.id)
        user_products = json.loads(user_products_json)
        product_id_list = list(user_products.keys())
        if not product_id_list:
            await message.answer(text="На данный момент таблица пуста.")
        else:
            answer_text = f'В таблице находятся {len(product_id_list)} объявлений:\n\n'
            for product_id in product_id_list:
                if product_id_list.index(product_id) > 9:
                    answer_text += f'и ещё {len(product_id_list)-10}...'
                    break
                else:
                    answer_text += f' - ID: {product_id}\n'
            await message.answer(
                text=answer_text,
                reply_markup=action_table_to_csv(message.from_user.id)
            )


@router.callback_query(SaveTableToFileCSV.filter())
async def save_to_csv(callback: types.CallbackQuery, callback_data: SaveTableToFileCSV):
    async with Database() as db:
        table_df = Table()
        user_products_json = await db.get_user_data(callback_data.user_id)
        user_products = json.loads(user_products_json)
        for product in user_products.values():
            table_df.push(product)
        csv_output_file_path = table_df.get_csv()
        csv_file_input = FSInputFile(csv_output_file_path, filename=csv_output_file_path)
        await callback.message.delete_reply_markup()
        await callback.message.answer_document(document=csv_file_input)
        del table_df


@router.message(Command("clear"))
async def show_table(message: types.Message):
    async with Database() as db:
        await db.update_user_data(message.from_user.id, '{}')
        await message.reply(text="Таблица очищена!", reply_markup=ReplyKeyboardRemove())
