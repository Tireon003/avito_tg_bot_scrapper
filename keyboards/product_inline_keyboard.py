from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from factories.add_to_table_fab import AddToTableCallbackFactory


def action_with_product_inline(action_key: str, product_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Actions, available for current keyboard
    actions = {
        "add": "Добавить объявление в таблицу",
        "pop": "Удалить объявление из таблицы"
    }

    # Action validation
    if action_key not in actions.keys():
        raise ValueError("Передано невалидное действие, разрешено только 'add' и 'pop'.")

    builder.button(
        text=actions[action_key],  # Label for inline-keyboard
        callback_data=AddToTableCallbackFactory(
            action=action_key,  # Action's name ("pop" or "add")
            value=product_id,  # Product's ID
            user_id=user_id  # Telegram user's ID
        )
    )

    return builder.as_markup()
