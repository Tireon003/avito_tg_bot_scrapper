from aiogram import types, Router
from aiogram.filters.command import Command
from modules.database.database import Database

router = Router()


# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    async with Database() as db:
        await db.add_user(message.from_user.id)
        await message.answer("Scrap from Avito.ru!")


@router.message(Command("table"))
async def show_table(message: types.Message):
    async with Database() as db:
        user_data = await db.get_user_data(message.from_user.id)
        await message.answer(user_data)


@router.message(Command("clear"))
async def show_table(message: types.Message):
    async with Database() as db:
        await db.update_user_data(message.from_user.id, '{}')
        await message.reply("Таблица очищена!")
