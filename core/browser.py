import threading
import os
from sys import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait


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
        options.add_argument('--disable-gpu')
        # Generate the browser.
        if platform == 'win32':
            driver_path = os.path.join(os.path.dirname(__file__),
                                       'chromedriver.exe')
        else:
            options.add_argument('--headless')
            driver_path = 'chromedriver'
        print('Starting browser...')
        self.browser = webdriver.Chrome(executable_path=driver_path,
                                        options=options)
        self.wait = WebDriverWait(self.browser, timeout=60)
        print('browser ready.')

    def shutdown(self):
        # Shutdown the browser.
        self.browser.quit()
