from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def categories_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for item in items:
        builder.add(KeyboardButton(text=item))
    builder.adjust(2)
    return builder.as_markup()

