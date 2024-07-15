from aiogram.fsm.state import StatesGroup, State


class ParseCategoryState(StatesGroup):
    choosing_category = State()
    choosing_subcategory = State()
    entering_number_of_products = State()
    choosing_location = State()
