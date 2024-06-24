from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import datetime
import re
import pandas as pd


class WebDriverManager:

    OPTIONS = webdriver.ChromeOptions().page_load_strategy = "eager"

    @classmethod
    def init_webdriver(cls):
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        return webdriver.Chrome(options=options)


class PageDataParser:

    XPATH_TAGS = {
        "ID": "//span[@data-marker='item-view/item-id']",  # Unique ID of product
        "DATE": "//span[@data-marker='item-view/item-date']",  # Date and time of publication
        "TITLE": "//h1[@data-marker='item-view/title-info']",  # Title of product
        "DESCRIPTION": "//div[@data-marker='item-view/item-description']",  # Description of product
        "PRICE": "//span[@data-marker='item-view/item-price']",  # Product's price (can be either integer or "Бесплатно" or "Цена не указана")
        "VIEWS": "//span[@data-marker='item-view/total-views']",  # Number of views on product's page
        "ADDRESS": "//span[@class='style-item-address__string-wt61A']",  # Seller's address
        "CATEGORY": "//div[@data-marker='breadcrumbs']"  # Category of the product
    }

    def __init__(self, url: str, driver=WebDriverManager.init_webdriver()):
        self.driver = driver
        self.url = url  # Потом реализовать проверку ссылки
        self.driver.get(url)

    def get_product_id(self) -> int:
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, self.XPATH_TAGS["ID"]))
        )
        return int(element.text[2:])

    def get_product_title(self) -> str:
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, self.XPATH_TAGS["TITLE"]))
        )
        return element.text

    def get_product_price(self) -> int:
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, self.XPATH_TAGS["PRICE"]))
        )
        return int(element.get_attribute("content"))

    def get_product_category_path(self) -> list:
        cat_list = []
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, self.XPATH_TAGS["CATEGORY"]))
        )
        cat_text = element.text
        cat_el = cat_text[0]
        for i in range(1, len(cat_text)):
            if cat_text[i-1].islower() and cat_text[i].isupper():
                cat_list.append(cat_el)
                cat_el = ""
            cat_el += cat_text[i]
            if i == len(cat_text) - 1:
                cat_list.append(cat_el)
        return cat_list[1:]

    def __call__(self, *args, **kwargs):
        """ Calling an instance to get dict of page data """

        page_data_dict = {
            "ID": self.get_product_id(),
            "TITLE": self.get_product_title(),
            "PRICE": self.get_product_price(),
            "CATEGORIES": self.get_product_category_path()
        }
        return page_data_dict


page1 = PageDataParser("https://www.avito.ru/mahachkala/telefony/samsung_galaxy_a50_464_gb_4143989571")

print(page1())
