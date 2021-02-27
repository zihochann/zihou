import threading
import os
from sys import platform
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait


def bin_name(name: str):
    return '{}.exe'.format(name) if platform == 'win32' else name


class Driver:
    _driver_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton check.
        if not hasattr(cls, '_instance'):
            with Driver._driver_lock:
                if not hasattr(cls, '_instance'):
                    Driver._instance = super().__new__(cls)
        # This is a singleton instance.
        return Driver._instance

    def __init__(self, *args, **kwargs):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        # Generate the driver.
        options = Options()
        options.add_argument('-headless')
        # Generate the browser.
        # Find the gecko driver.
        driver_path = os.path.join(os.path.dirname(__file__), bin_name(
            'geckodriver'))
        self.browser = webdriver.Firefox(executable_path=driver_path,
                                         options=options)
        self.wait = WebDriverWait(self.browser, timeout=60)

    def shutdown(self):
        # Shutdown the browser.
        self.browser.quit()
