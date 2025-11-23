# import allure
from typing import Optional
from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Optional[Page] = None):
        self.page = page

    def go_back(self):
       self.page.go_back()