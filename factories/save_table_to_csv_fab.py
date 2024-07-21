from aiogram.filters.callback_data import CallbackData


class SaveTableToFileCSV(CallbackData, prefix='save_csv_fab'):
    user_id: int
