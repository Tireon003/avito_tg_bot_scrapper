from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from datetime import timedelta, date
import time
import re

# todo Главная проблема: обойти блокировки по IP!


class WebDriverManager:

    __options = webdriver.ChromeOptions()

    def __init__(self):
        self.__options.page_load_strategy = "eager"
        self.__options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=self.__options)
        print("Драйвен инициализирован")  # debug for devs

    def init_webdriver(self):
        print("Драйвер запущен")  # debug for devs
        return self.driver

    def close_webdriver(self):
        print("Драйвер удален")  # debug for devs
        self.driver.close()


class PageDataParser:
    """
    Class PageDataParser contains logic of parsing data from product's page

    Input arguments:
     - url: URL-address of product's page, string data
     - driver: instance of webdriver.

    """

    ID = "//span[@data-marker='item-view/item-id']"  # Unique ID of product
    DATE = "//span[@data-marker='item-view/item-date']"  # Date and time of publication
    TITLE = "//h1[@data-marker='item-view/title-info']"  # Title of product
    DESCRIPTION = "//div[@data-marker='item-view/item-description']"  # Description of product
    PRICE = "//span[@data-marker='item-view/item-price']"  # Product's price
    VIEWS = "//span[@data-marker='item-view/total-views']"  # Number of views on product's page
    ADDRESS = "//span[@class='style-item-address__string-wt61A']"  # Seller's address
    CATEGORY = "//div[@data-marker='breadcrumbs']"  # Category of the product

    def __init__(self, url: str, driver: webdriver):
        #  todo Когда буду делать парсинг данных асинхронно, добавить сохранение и изменение контекста вкладки
        #  todo Реализоваь функцию, которая будет открывать новую вкладку в браузере и сохранять контекст вкладки
        #  todo При использовании close() будет удаляться вкладка на которой фокус т.е на текущей
        self.driver = driver
        self.url = self.verify_url(url)
        self.driver.implicitly_wait(10)

    def verify_url(self, url):
        if not isinstance(url, str):
            raise TypeError("Ссылка должна быть строкой")
        elif not url.startswith("https://www.avito.ru/"):
            raise ValueError("Ссылка должна иметь домен www.avito.ru")
        elif not url:
            raise ValueError("Ссылка должна быть непустой строкой")
        try:
            self.driver.get(url)
        except Exception:
            print("Ссылка не корректна!")

    def get_product_id(self) -> int:
        element = self.driver.find_element(By.XPATH, self.ID)
        return int(element.text[2:])

    def get_product_title(self) -> str:
        element = self.driver.find_element(By.XPATH, self.TITLE)
        return element.text

    def get_product_price(self) -> str:
        element = self.driver.find_element(By.XPATH, self.PRICE)
        return element.get_attribute("content")

    def get_product_category_path(self) -> list:
        cat_list = []
        elements = self.driver.find_elements(By.XPATH, "//span[@itemprop='itemListElement']")
        for item in elements:
            cat_list.append(item.text)
        return cat_list[1:]

    def get_product_date(self) -> str:
        element = self.driver.find_element(By.XPATH, self.DATE)
        time_pattern = r'\b\d{1,2}:\d{2}\b'  # re for cut time from string
        if "вчера" in element.text:
            return " ".join(map(
                str, (date.today() - timedelta(days=1), re.search(time_pattern, element.text).group(0))
            ))
        elif "сегодня" in element.text:
            return " ".join(map(str, (date.today(), re.search(time_pattern, element.text).group(0))))
        else:
            return element.text[2:]

    def get_product_description(self) -> str:
        element = self.driver.find_element(By.XPATH, self.DESCRIPTION)
        return element.text

    def get_product_total_views(self) -> int:
        element = self.driver.find_element(By.XPATH, self.VIEWS)
        total_views = int(element.text.split()[0])
        return total_views

    def get_product_address(self) -> str:
        element = self.driver.find_element(By.XPATH, self.ADDRESS)
        return element.text

    def get_product_specs(self) -> list:
        specs_xpath = "//div[@data-marker='item-view/item-params']"
        elements = self.driver.find_elements(By.XPATH, specs_xpath)
        if not len(elements):
            return []
        elements = elements[-1].find_elements(By.XPATH, "./ul/li")
        product_specs = []
        for item in elements:
            item_spec_name = item.find_element(By.TAG_NAME, "span").text
            item_spec_value = item.text.replace(item_spec_name, '').strip()
            item_spec_name = item_spec_name.strip(":")
            product_specs.append((item_spec_name, item_spec_value))
        return product_specs

    def __call__(self, *args, **kwargs):
        """ Method to get dict of page's data """

        page_data_dict = {
            "ID": self.get_product_id(),
            "TITLE": self.get_product_title(),
            "DATE": self.get_product_date(),
            "PRICE": self.get_product_price(),
            "ADDRESS": self.get_product_address(),
            "CATEGORIES": self.get_product_category_path(),
            "DESCRIPTION": self.get_product_description(),
            "VIEWS": self.get_product_total_views(),
            "SPECS": self.get_product_specs()
        }
        return page_data_dict


class SearchFilter:
    pass


class CategoryParser:

    def __init__(self, new_driver: webdriver):
        self.driver = new_driver
        self.driver.get("https://www.avito.ru/")
        self.driver.implicitly_wait(6)

    @staticmethod
    def verify_location(location: str):
        location_without_dash = location.replace("-", "")
        if not location_without_dash.isalpha():
            return "Некорректное наименование локации!"
        return location.title().strip()

    def filter_configuration(self):
        pass

    def get_category_list(self):

        """ Method returns list of web elements of categories """

        show_categories_xpath = '//button[@data-marker="top-rubricator/all-categories"]'
        show_categories_button_element = self.driver.find_element(By.XPATH, show_categories_xpath)
        show_categories_button_element.click()
        time.sleep(1)
        category_list_xpath = '//div[@class="new-rubricator-content-leftcontent-_hhyV"]'
        category_list_elements = self.driver.find_elements(By.XPATH, category_list_xpath)
        return category_list_elements

    def set_category(self):
        """
        Метод будет принимать в себя выбранный пользователем элемент (категорию)
        Метод будет так же, как и get_category_list, переходить в раздел категорий, и фокусироваться на нужной

        :return: Список подкатегорий данный категории
        """
        pass

    def set_subcategory(self):
        """
        На вход поступает элемент списка подкатегории.
        Затем метод кликает на выбранный пользоватетем пункт
        По окончании работы метода загружается страница с объявлениями выбранной категории и подкатегории.

        :return: Метод возвращает ссылку на открытую страницу *self.driver.current_url
        """

        pass

    # todo создать метод get_sort_settings() -> element, затем можно нужный элемент передавать в данный метод
    def change_sort_method(self, sort_method_value):
        sort_settings_button_xpath = '//span[@data-marker="sort/title"]'
        choose_sort_element = self.driver.find_element(By.XPATH, sort_settings_button_xpath)
        choose_sort_element.click()
        # Если на вход будем получать сразу нужный элемент, то можно сразу сделать клик на элемент и все
        sort_methods_list_xpath = '//div[@data-marker="sort/dropdown"]'
        sort_methods_elements = self.driver.find_elements(By.XPATH, sort_methods_list_xpath)
        for item in sort_methods_elements:
            if item.text.strip().lower() == sort_method_value.strip().lower():
                item.click()
                return f'Метод сортировки изменен на {sort_method_value.capitalize()}'
        else:
            sort_methods_elements[0].click()
            return f"Метод сортировки не изменен"

    def set_search_location(self, location_name: str):
        location_name = self.verify_location(location_name)
        current_location_xpath = '//div[@data-marker="search-form/change-location"]'
        element = self.driver.find_element(By.XPATH, current_location_xpath)
        element.click()
        input_location_xpath = "//input[@data-marker='popup-location/region/search-input']"
        input_location_element = self.driver.find_element(By.XPATH, input_location_xpath)
        input_location_element.click()
        input_location_element.clear()
        time.sleep(1)
        input_location_element.send_keys(location_name)
        time.sleep(1)
        found_locations_xpath = "//button[@data-marker='popup-location/region/custom-option([object Object])']"
        found_locations_list = self.driver.find_elements(By.XPATH, found_locations_xpath)
        for item in found_locations_list:
            print(item.text)
            if location_name == item.text.strip() or location_name + "," in item.text.strip():
                item.click()
                break
        else:
            found_locations_list[0].click()
        apply_changes_element_xpath = "//button[@data-marker='popup-location/save-button']"
        apply_button = self.driver.find_element(By.XPATH, apply_changes_element_xpath)
        apply_button.click()
        time.sleep(2)
        new_location_element = self.driver.find_element(By.XPATH, current_location_xpath)
        return f"Локация для поиска изменена на {new_location_element.text} или похожую"

#  code debug


manager = WebDriverManager()  # Создается экземпляр драйвера
my_driver = manager.init_webdriver()  # Получаем ссылку на созданный драйвер
index_page = CategoryParser(my_driver)  # Используем драйвер в нужном классе
print(index_page.set_search_location("Махачкала"))  # Проверка работы метода смены локации поиска объявлений


for i in index_page.get_category_list():
    print(i.text)
    time.sleep(1)

del index_page  # Удаляем объект CategoryParser, удостоверились, что драйвер продолжает работу

# Проверяем работу парсера данных со страницы объявления
page1 = PageDataParser("https://www.avito.ru/moskva/vodnyy_transport/novaya_parusnaya_yahta_antila_26_classik_pr.belarus_1175058901", my_driver)

# Выводим информацию, которую мы спарсили в виде <Ключ> - <Значение>.
for key, value in page1().items():
    print(key, value, sep=" - ")

# Закрываем вкладку бразуера (если вкладка последняя, то окно), теперь драйвер можно удалять
manager.close_webdriver()

