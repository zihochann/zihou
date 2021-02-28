import threading
import time
from core.browser import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as expected

TEST_MESSAGE = 'このツイートは自動ボットから送信されるテストツイートです。後で削除されます。'
SENDING_URL = 'https://twitter.com/home'
MAX_TRIALS = 3


class MessageSender:
    _driver_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton check.
        if not hasattr(cls, '_instance'):
            with MessageSender._driver_lock:
                if not hasattr(cls, '_instance'):
                    MessageSender._instance = super().__new__(cls)
        # This is a singleton instance.
        return MessageSender._instance

    def __init__(self, *args, **kwargs):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        # Login in the driver.
        print('Starting driver...')
        self.driver = Driver()
        print('Driver ready.')
        # Save the username and password.
        self.buf_u = ''
        self.buf_p = ''

    def shutdown(self):
        # Disable the driver.
        self.driver.shutdown()
        
    def __execute_login(self, buf_u, buf_p):
        print('doing login...')
        # Not try for empty data.
        if len(buf_u) == 0 or len(buf_p) == 0:
            return False
        div_form = self.driver.browser.find_elements_by_tag_name('form')[0]
        # Now locate to username and password
        login_labels = div_form.find_elements_by_tag_name('label')
        # There should be 2 of these.
        if len(login_labels) != 2:
            raise Exception('Failed to parse twitter login.')
        # Now extract the input from those two element.
        username_input = None
        password_input = None
        for label in login_labels:
            tag_input = label.find_element_by_tag_name('input')
            tag_name = tag_input.get_attribute('name')
            # Check the tag.
            if 'username' in tag_name:
                username_input = tag_input
            elif 'password' in tag_name:
                password_input = tag_input
        # Input the data.
        username_input.send_keys(buf_u)
        time.sleep(0.5)
        password_input.send_keys(buf_p)
        time.sleep(0.5)

        # Find the login button.
        def find_login(parent):
            possible_divs = parent.find_elements_by_tag_name('div')
            for button_div in possible_divs:
                button_role = button_div.get_attribute('role')
                if button_role == 'button':
                    return button_div
            return None

        login_button = find_login(div_form)
        if login_button is None:
            raise Exception('Failed to find login button.')
        # Click the login button.
        login_button.click()
        # Find all the input tags.
        try:
            self.driver.wait.until(
                expected.visibility_of_element_located((By.TAG_NAME, 'main')))
        except:
            return False
        # Check whether the url contains error and login.
        web_url = self.driver.browser.current_url
        if 'error' in web_url:
            return False
        # Save the username and password.
        self.buf_u = buf_u
        self.buf_p = buf_p
        print('complete?')
        return True

    def login(self, buf_u, buf_p):
        # Goto login
        try:
            print('launching login URL...')
            self.driver.browser.get('https://twitter.com/login')
            self.driver.wait.until(
                expected.visibility_of_element_located((By.TAG_NAME, 'form')))
        except:
            return False
        return self.__execute_login(buf_u, buf_p)

    def send_message(self, message: str):
        # Go to the home page of the twitter.
        if self.driver.browser.current_url != SENDING_URL:
            self.driver.browser.get(SENDING_URL)
            # Hold and wait whether the send message is correct.
            try:
                self.driver.wait.until(
                    expected.visibility_of_element_located((By.TAG_NAME, 'main')))
            except:
                return False
            # If the url contains login, we have to login.
            web_url = self.driver.browser.current_url
            if 'login' in web_url and \
                not self.__execute_login(self.buf_u, self.buf_p):
                return False
        # Access and wait until the input box appears.
        try:
            self.driver.wait.until(expected.visibility_of_element_located(
                (By.CLASS_NAME, 'public-DraftEditor-content')))
        except:
            return False
        # Set the content.
        editor = self.driver.browser.find_element_by_class_name(
            'public-DraftEditor-content')
        editor.send_keys(message)
        # Trial for 3 times.
        trials = 0
        # while trials < 3:
        success_flag = False
        for _ in range(MAX_TRIALS):
            editor = self.driver.browser.find_element_by_class_name(
                'public-DraftEditor-content')
            # Click CTRL+Enter to send it.
            editor.send_keys(Keys.CONTROL, Keys.ENTER)
            # Wait for 0.5 seconds.
            time.sleep(0.5)
            # Check whether there is error message.
            try:
                # Hold and wait until it executes?
                self.driver.wait.until(expected.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-testid="toolBar"]')))
            except:
                return False
            # Also hold for 0.5 seconds.
            time.sleep(0.5)
            try:
                div_error = self.driver.browser.find_element_by_css_selector('div[role="alert"]')
            except:
                # No error found!
                success_flag = True
                break
            # CD for 2 seconds for next trial.
            time.sleep(2)
        # CD for 2 seconds.
        time.sleep(2)
        return success_flag
