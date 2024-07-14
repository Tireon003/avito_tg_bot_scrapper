from aiogram.filters.callback_data import CallbackData


class AddToTableCallbackFactory(CallbackData, prefix='addtotable_fab'):
    action: str
    value: int
    user_id: int
