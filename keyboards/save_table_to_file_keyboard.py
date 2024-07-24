from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from factories.save_table_to_csv_fab import SaveTableToFileCSV
from modules.table_manager import Table


def action_table_to_csv(user_id: int, table_df: Table()) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Сохранить в формате .csv",
        callback_data=SaveTableToFileCSV(user_id=user_id)
    )
    return builder.as_markup()
