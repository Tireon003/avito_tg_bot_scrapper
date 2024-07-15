from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from keyboards.select_category_keyboard import categories_keyboard
from modules.scrapper import WebDriverManager, CategoryParser, PageDataParser
from states.parse_category_state import ParseCategoryState

router = Router()

# todo Здесь реализовать логигу парса категории в виде конечного автомата.


@router.message(Command("category"), StateFilter(None))
async def init_category_parse(message: types.Message, state: FSMContext):
    driver = WebDriverManager()
    category_parser = CategoryParser(driver.init_webdriver())
    item_elements = category_parser.get_category_list()
    items_title = [el.text for el in item_elements]

    await message.answer(
        text="Выберите категорию:",
        reply_markup=categories_keyboard(items_title)
    )
    await state.set_state(ParseCategoryState.choosing_category)
