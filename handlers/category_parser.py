import os
from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from keyboards.select_category_keyboard import categories_keyboard
from keyboards.select_subcategory_keyboard import subcategories_keyboard
from modules.scrapper import WebDriverManager, CategoryParser
from modules.table_manager import Table
from states.parse_category_state import ParseCategoryState

router: Router = Router()


@router.message(Command("cancel"))
async def cancel_category_parser(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    state_data = await state.get_data()
    driver = state_data["driver"]
    if current_state is None:
        await message.answer(
            text="В данный момент отменять нечего.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            text="Парсинг отменен.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        driver.close_webdriver()


@router.message(Command("category"), StateFilter(None))
async def init_category_parse(message: types.Message, state: FSMContext) -> None:
    driver = WebDriverManager()
    table = Table()
    category_parser = CategoryParser(driver.init_webdriver())
    category_label_elements = category_parser.get_category_list()
    categories_title = list([el.text for el in category_label_elements])
    await state.update_data(
        cat_titles=categories_title,
        cat_elements=category_label_elements,
        table=table,
        driver=driver,
        parser=category_parser
    )
    await message.answer(
        text="Выберите категорию:",
        reply_markup=categories_keyboard(categories_title)
    )
    await state.set_state(ParseCategoryState.choosing_category)


@router.message(ParseCategoryState.choosing_category)
async def category_is_chosen(message: types.Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    driver = state_data["driver"]
    parser = state_data["parser"]
    if message.text in state_data['cat_titles']:
        parser.set_category(state_data['cat_elements'][state_data['cat_titles'].index(message.text)])
        subcategory_label_elements = parser.get_subcategories()
        subcategories_title = [el.text.strip() for el in subcategory_label_elements]
        await state.update_data(
            subcat_titles=subcategories_title,
            subcat_elements=subcategory_label_elements,
            driver=driver,
            parser=parser
        )
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
        del parser
        driver.close_webdriver()


@router.message(ParseCategoryState.choosing_subcategory)
async def subcategory_is_chosen(message: types.Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    driver = state_data["driver"]
    parser = state_data["parser"]
    if message.text in state_data['subcat_titles']:
        category_url = parser.set_subcategory(
            selected_subcategory_element=state_data['subcat_elements'][state_data['subcat_titles'].index(message.text)]
        )
        await state.update_data(url=category_url)
        await message.answer(
            text="Введите наименование населенного пункта или региона для поиска:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(ParseCategoryState.choosing_location)
    else:
        await message.answer(
            text="Введенной подкатегории не существует, отмена операции.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        del parser
        driver.close_webdriver()


@router.message(ParseCategoryState.choosing_location)
async def location_is_chosen(message: types.Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    parser = state_data["parser"]
    parser.set_search_location(message.text)
    await message.answer(
        text="Отлично. Теперь введите нужное количество объявлений. Максимум: 100. Если в категории количество " +
             "объявлений меньше, чем вы указали, будет получено столько, скольки доступно.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ParseCategoryState.entering_number_of_products)


@router.message(ParseCategoryState.entering_number_of_products)
async def number_of_products_entered(message: types.Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    table = state_data['table']
    driver = state_data["driver"]
    parser = state_data["parser"]
    products_number = message.text
    category_url = state_data['url']
    if not products_number.isdigit() or 1 > int(products_number) > 100:
        await message.answer(
            text="Введен неверный формат числа. Отмена операции...",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        products_number = int(products_number)
        category_gen = parser.parse_products(
            number_of_products=products_number,
            url=category_url
        )
        for item in category_gen:
            text_answer = f'ID {item["ID"]} parsed'
            table.push(item)
            await message.answer(text=text_answer)
        else:
            csv_filepath = table.get_csv()
            csv_file = FSInputFile(csv_filepath, filename=csv_filepath)
            await message.answer(text="Парсинг полностью завершен!")
            await message.answer_document(
                document=csv_file
            )
            os.remove(csv_filepath)
    await state.clear()
    del parser
    driver.close_webdriver()
