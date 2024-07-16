from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from keyboards.select_category_keyboard import categories_keyboard
from keyboards.select_subcategory_keyboard import subcategories_keyboard
from modules.scrapper import WebDriverManager, CategoryParser, PageDataParser
from states.parse_category_state import ParseCategoryState

router = Router()

# todo перенести хранение данных в state
# если оставить так, то когда 2 и более юзера будут пользоваться парсом категории будет либо ошибка либо будет парс неверной категории
category_label_elements: list = []
categories_title: list[str] = []
subcategory_label_elements: list = []
subcategories_title: list[str] = []
driver: WebDriverManager
category_parser: CategoryParser


@router.message(Command("category"), StateFilter(None))
async def init_category_parse(message: types.Message, state: FSMContext):
    global category_label_elements, \
        categories_title, \
        driver, \
        category_parser

    driver = WebDriverManager()
    category_parser = CategoryParser(driver.init_webdriver())
    category_label_elements = category_parser.get_category_list()
    categories_title = [el.text for el in category_label_elements]
    await message.answer(
        text="Выберите категорию:",
        reply_markup=categories_keyboard(categories_title)
    )
    await state.set_state(ParseCategoryState.choosing_category)


@router.message(ParseCategoryState.choosing_category, F.text.in_(categories_title))
async def category_is_chosen(message: types.Message, state: FSMContext):
    global category_label_elements, \
        categories_title, \
        driver, \
        category_parser, \
        subcategories_title, \
        subcategory_label_elements

    #await state.update_data(chosen_category=category_label_elements[categories_title.index(message.text)])
    chosen_category = category_label_elements[categories_title.index(message.text)]
    subcategory_label_elements = category_parser.get_subcategories()
    subcategories_title = [el.text for el in subcategory_label_elements]
    await message.answer(
        text="Отлично, теперь выберите подкатегорию:",
        reply_markup=subcategories_keyboard(subcategories_title)
    )
    await state.set_state(ParseCategoryState.choosing_subcategory)

# todo При вводе верной категории срабатывает данный хендлер, исправить
@router.message(ParseCategoryState.choosing_category)
async def non_existant_category(message: types.Message, state: FSMContext):
    global category_parser, driver
    await message.answer(
        text="Введенной категории не существует, отмена операции.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    del category_parser
    driver.close_webdriver()
