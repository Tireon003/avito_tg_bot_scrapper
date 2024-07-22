from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from datetime import timedelta, date
import time
import re

from selenium.webdriver.remote.webelement import WebElement


class WebDriverManager:

    __options = webdriver.ChromeOptions()

    def __init__(self):
        self.__options.page_load_strategy = "eager"
        # self.__options.add_argument('--headless')  # makes browser's window not visible
        self.__options.add_experimental_option("detach", True)
        self.__options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.__options.add_experimental_option('useAutomationExtension', False)
        self.__options.add_argument("--disable-blink-features=AutomationControlled")
        self.__options.add_argument(f"--disable-blink-features=AutomationControlled")
        self.__options.add_argument(
            f"--user-agent=Mozilla/5.0 (X11; Linux x86_64) " +
            f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=self.__options)
        print("Драйвен инициализирован")  # debug for devs

    def init_webdriver(self):
        print("Драйвер запущен")  # debug for devs
        return self.driver

    def close_webdriver(self):
        print("Драйвер завершил работу")  # debug for devs
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
        self.driver = driver
        self.url = self.verify_url(url)
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)

    @staticmethod
    def verify_url(url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("Ссылка должна быть строкой")
        elif not url.startswith("https://www.avito.ru/"):
            raise ValueError("Ссылка должна иметь домен www.avito.ru")
        elif not url:
            raise ValueError("Ссылка должна быть непустой строкой")
        else:
            return url

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
        try:
            element = self.driver.find_element(By.XPATH, self.ADDRESS)
            return element.text
        except NoSuchElementException:
            return "Empty"

    def get_product_specs(self) -> list:
        specs_xpath = "//div[@data-marker='item-view/item-params']"
        elements = self.driver.find_elements(By.XPATH, specs_xpath)
        if not len(elements):
            return []
        product_specs = []
        for section in elements:
            section_ul_li = section.find_elements(By.XPATH, "./ul/li")
            for item in section_ul_li:
                item_spec_name = item.find_element(By.TAG_NAME, "span").text
                item_spec_value = item.text.replace(item_spec_name, '').strip()
                item_spec_name = item_spec_name.strip(":")
                product_specs.append((item_spec_name, item_spec_value))
        return product_specs

    def __call__(self, *args, **kwargs):
        """ Method to get dict of page's data """
        time.sleep(2)
        page_data_dict = {
            "ID": self.get_product_id(),
            "TITLE": self.get_product_title(),
            "DATE": self.get_product_date(),
            "PRICE": self.get_product_price(),
            "ADDRESS": self.get_product_address(),
            "CATEGORIES": self.get_product_category_path(),
            "DESCRIPTION": self.get_product_description(),
            "VIEWS": self.get_product_total_views(),
            "SPECS": str(self.get_product_specs())
        }
        return page_data_dict


class CategoryParser:

    __MAX_COUNT_OF_PAGES = 100

    def __init__(self, new_driver: webdriver):
        self.driver = new_driver
        self.driver.get("https://www.avito.ru/")
        self.driver.implicitly_wait(7)

    @staticmethod
    def verify_location(location: str) -> str:
        location_without_dash = location.replace("-", "")
        if not location_without_dash.isalpha():
            return "Некорректное наименование локации!"
        return location.title().strip()

    def get_category_list(self) -> WebElement:
        """
        Method opens modal window which allows to user to select category and subcategory.
        :return: iterable object which contains webelements of each category
        """
        time.sleep(4)
        show_categories_xpath = '//button[@data-marker="top-rubricator/all-categories"]'
        show_categories_button_element = self.driver.find_element(By.XPATH, show_categories_xpath)
        show_categories_button_element.click()
        time.sleep(1)
        category_list_xpath = '//div[@class="new-rubricator-content-leftcontent-_hhyV"]/div[@data-marker]'
        category_list_elements = self.driver.find_elements(By.XPATH, category_list_xpath)
        return category_list_elements

    def set_category(self, chosen_category: WebElement):
        """
        Method selects the category selected by the user.
        Required conditions:
         - Modal window with all categories is visible.
        :param chosen_category: a webelement of category selected by user
        :return: String-message that notifies that the category has been selected
        """
        category_list_xpath = '//div[@class="new-rubricator-content-leftcontent-_hhyV"]'
        if not len(self.driver.find_elements(By.XPATH, category_list_xpath)):
            raise NoSuchElementException("На странице в данный момент времени нет окна выбора категории.")
        chosen_category.click()

    def get_subcategories(self) -> WebElement:
        """
        Required conditions in which method can work correct:
         - Modal window to choose category is visible.
         - Category is selected (method set_category was called before current method)
        :return: Iterable object which contains all found subcategories
        """
        show_more_buttons_xpath = '//button[@data-marker="top-rubricator/more-button"]'
        show_more_button_elements = self.driver.find_elements(By.XPATH, show_more_buttons_xpath)
        for button in show_more_button_elements:
            button.click()
        subcategories = self.driver.find_elements(
            By.XPATH,
            '//a[@data-name and @data-cid]'
        )
        return subcategories

    def set_subcategory(self, selected_subcategory_element: WebElement) -> str:
        """
        The method clicks on the subcategories selected by the user to open a page with products of this subcategory.
        :param selected_subcategory_element: a webelement of subcategory selected by user
        :return: URL of opened page
        """
        selected_subcategory_element.click()
        time.sleep(0.5)
        return self.driver.current_url

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

    def parse_products(self, number_of_products: int, url: str):
        if self.driver.current_url != url and not url:
            self.driver.get(url)
        time.sleep(3)
        product_xpath = '//a[@data-marker="item-title"]'
        pagination_items_xpath = '//ul[@data-marker="pagination-button"]/li'
        total_count_of_products = self.driver.find_element(
            By.XPATH,
            '//span[@data-marker="page-title/count"]'
        ).text
        total_count_of_products = total_count_of_products.replace(" ", "")
        total_count_of_products = min(int(total_count_of_products), number_of_products, self.__MAX_COUNT_OF_PAGES)
        print(total_count_of_products, number_of_products)
        number_of_webpages_to_parse = total_count_of_products // 50 + 1
        products_remaining = total_count_of_products
        for i in range(number_of_webpages_to_parse):
            products_list = self.driver.find_elements(By.XPATH, product_xpath)
            main_window = self.driver.current_window_handle
            for product in products_list:
                product.click()
                all_windows = self.driver.window_handles
                new_window = [window for window in all_windows if window != main_window][0]
                print(*[window for window in all_windows if window != main_window])
                self.driver.switch_to.window(new_window)
                current_page = PageDataParser(self.driver.current_url, self.driver)
                yield current_page()
                del current_page
                self.driver.close()
                self.driver.switch_to.window(main_window)
                products_remaining -= 1
                if products_remaining == 0:
                    return len(products_list)
            if i < number_of_webpages_to_parse - 1:
                next_page_button = self.driver.find_elements(
                    By.XPATH,
                    pagination_items_xpath
                )[-1]
                next_page_button.click()
                time.sleep(2)
