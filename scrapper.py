from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from datetime import timedelta, date
import re


class WebDriverManager:

    OPTIONS = webdriver.ChromeOptions().page_load_strategy = "eager"

    @classmethod
    def init_webdriver(cls):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        return webdriver.Chrome(options=options)


class PageDataParser:

    ID = "//span[@data-marker='item-view/item-id']"  # Unique ID of product
    DATE = "//span[@data-marker='item-view/item-date']"  # Date and time of publication
    TITLE = "//h1[@data-marker='item-view/title-info']"  # Title of product
    DESCRIPTION = "//div[@data-marker='item-view/item-description']"  # Description of product
    PRICE = "//span[@data-marker='item-view/item-price']"  # Product's price
    VIEWS = "//span[@data-marker='item-view/total-views']"  # Number of views on product's page
    ADDRESS = "//span[@class='style-item-address__string-wt61A']"  # Seller's address
    CATEGORY = "//div[@data-marker='breadcrumbs']"  # Category of the product

    def __init__(self, url: str, driver=WebDriverManager.init_webdriver()):
        self.driver = driver
        self.url = self.verify_url(url)
        self.driver.implicitly_wait(7)

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
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, self.DATE))
        )
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
            "CATEGORIES": self.get_product_category_path(),
            "DESCRIPTION": self.get_product_description(),
            "VIEWS": self.get_product_total_views(),
            "SPECS": self.get_product_specs()
        }
        return page_data_dict


page1 = PageDataParser("https://www.avito.ru/mahachkala/produkty_pitaniya/shokolad_molochnyy_6_kg_4036950274")

for key, value in page1().items():
    print(key, value, sep=" - ")
