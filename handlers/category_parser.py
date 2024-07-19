import json

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
    categories_title = list([el.text for el in category_label_elements])
    print(categories_title)

    await message.answer(
        text="Выберите категорию:",
        reply_markup=categories_keyboard(categories_title)
    )
    await state.set_state(ParseCategoryState.choosing_category)


@router.message(ParseCategoryState.choosing_category)  # (, F.text.in_(categories_title))
async def category_is_chosen(message: types.Message, state: FSMContext):
    global category_label_elements, \
        categories_title, \
        driver, \
        category_parser, \
        subcategories_title, \
        subcategory_label_elements
    if message.text in categories_title:
        category_parser.set_category(category_label_elements[categories_title.index(message.text)])
        subcategory_label_elements = category_parser.get_subcategories()
        subcategories_title = [el.text.strip() for el in subcategory_label_elements]
        await message.answer(
            text="Отлично, теперь выберите подкатегорию:",
            reply_markup=subcategories_keyboard(subcategories_title)
        )
        await state.set_state(ParseCategoryState.choosing_subcategory)
    else:
        await message.answer(
            text="Введенной категории не существует, отмена операции.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        del category_parser
        driver.close_webdriver()


@router.message(ParseCategoryState.choosing_subcategory)
async def subcategory_is_chosen(message: types.Message, state: FSMContext):
    global driver, \
        category_parser, \
        subcategories_title, \
        subcategory_label_elements
    if message.text in subcategories_title:
        category_url = category_parser.set_subcategory(
            selected_subcategory_element=subcategory_label_elements[subcategories_title.index(message.text)]
        )
        await state.update_data(url=category_url)
        await message.answer(
            text="Отлично. Теперь введите нужное количество объявлений. Максимум: 100. Если в категории количество " +
                 "объявлений меньше, чем вы указали, будет получено столько, скольки доступно.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(ParseCategoryState.entering_number_of_products)
    else:
        await message.answer(
            text="Введенной подкатегории не существует, отмена операции.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        del category_parser
        driver.close_webdriver()


@router.message(ParseCategoryState.entering_number_of_products)
async def number_of_products_entered(message: types.Message, state: FSMContext):
    global category_parser
    state_data = await state.get_data()
    products_number = message.text
    category_url = state_data['url']
    if not products_number.isdigit() or 1 > int(products_number) > 100:  # todo условие неверно отрабаывает, переписать
        await message.answer(
            text="Введен неверный формат числа. Отмена операции...",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        del category_parser
        driver.close_webdriver()
    else:
        products_number = int(products_number)
        category_gen = category_parser.parse_products(
            number_of_products=products_number,
            url=category_url
        )

        for item in category_gen:
            text_answer = ''
            for key, value in item.items():
                text_answer += f'{key}: {str(value)[:300]}\n'
            await message.answer(text=text_answer)
        else:
            await message.answer("Парсинг полностью завершен!")

        await state.clear()
        del category_parser
        driver.close_webdriver()
