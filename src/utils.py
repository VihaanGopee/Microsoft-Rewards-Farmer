import contextlib
import time
import urllib.parse

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from .constants import BASE_URL


class Utils:
    def __init__(self, webdriver: WebDriver):
        self.webdriver = webdriver

    def waitUntilVisible(self, by: str, selector: str, timeToWait: float = 10):
        WebDriverWait(self.webdriver, timeToWait).until(
            ec.visibility_of_element_located((by, selector))
        )

    def waitUntilClickable(self, by: str, selector: str, timeToWait: float = 10):
        WebDriverWait(self.webdriver, timeToWait).until(
            ec.element_to_be_clickable((by, selector))
        )

    def waitForMSRewardElement(self, by: str, selector: str):
        loadingTimeAllowed = 5
        refreshsAllowed = 5

        checkingInterval = 0.5
        checks = loadingTimeAllowed / checkingInterval

        tries = 0
        refreshCount = 0
        while True:
            try:
                self.webdriver.find_element(by, selector)
                return True
            except Exception:  # pylint: disable=broad-except
                if tries < checks:
                    tries += 1
                    time.sleep(checkingInterval)
                elif refreshCount < refreshsAllowed:
                    self.webdriver.refresh()
                    refreshCount += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

    def waitUntilQuestionRefresh(self):
        return self.waitForMSRewardElement(By.CLASS_NAME, "rqECredits")

    def waitUntilQuizLoads(self):
        return self.waitForMSRewardElement(By.XPATH, '//*[@id="rqStartQuiz"]')

    def resetTabs(self):
        try:
            curr = self.webdriver.current_window_handle

            for handle in self.webdriver.window_handles:
                if handle != curr:
                    self.webdriver.switch_to.window(handle)
                    time.sleep(0.5)
                    self.webdriver.close()
                    time.sleep(0.5)

            self.webdriver.switch_to.window(curr)
            time.sleep(0.5)
            self.goHome()
        except Exception:  # pylint: disable=broad-except
            self.goHome()

    def goHome(self):
        currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
        targetUrl = urllib.parse.urlparse(BASE_URL)
        if (
            currentUrl.hostname != targetUrl.hostname
            or currentUrl.path != targetUrl.path
        ):
            self.webdriver.get(BASE_URL)
            self.waitUntilVisible(By.ID, "daily-sets", 10)
        self.tryDismissCookieBanner()

    def getAnswerCode(self, key: str, string: str) -> str:
        t = sum(ord(string[i]) for i in range(len(string)))
        t += int(key[-2:], 16)
        return str(t)

    def getDashboardData(self) -> dict:
        return self.webdriver.execute_script("return dashboard")

    def getAccountPoints(self) -> int:
        return self.getDashboardData()["userStatus"]["availablePoints"]

    def tryDismissAllMessages(self):
        buttons = [
            (By.ID, "iLandingViewAction"),
            (By.ID, "iShowSkip"),
            (By.ID, "iNext"),
            (By.ID, "iLooksGood"),
            (By.ID, "idSIButton9"),
            (By.CSS_SELECTOR, ".ms-Button.ms-Button--primary"),
        ]
        result = False
        for button in buttons:
            try:
                self.webdriver.find_element(button[0], button[1]).click()
                result = True
            except Exception:  # pylint: disable=broad-except
                continue
        return result

    def tryDismissCookieBanner(self):
        with contextlib.suppress(Exception):
            self.webdriver.find_element(By.ID, "cookie-banner").find_element(
                By.TAG_NAME, "button"
            ).click()
            time.sleep(2)

    def tryDismissBingCookieBanner(self):
        with contextlib.suppress(Exception):
            self.webdriver.find_element(By.ID, "bnp_btn_accept").click()
            time.sleep(2)

    def switchToNewTab(self, timeToWait: int = 0):
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[1])
        if timeToWait > 0:
            time.sleep(timeToWait)

    def closeCurrentTab(self):
        self.webdriver.close()
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[0])
        time.sleep(0.5)

    def visitNewTab(self, timeToWait: int = 0):
        self.switchToNewTab(timeToWait)
        self.closeCurrentTab()

    def getRemainingSearches(self):
        dashboard = self.getDashboardData()
        searchPoints = 1
        counters = dashboard["userStatus"]["counters"]
        if "pcSearch" not in counters:
            return 0, 0
        progressDesktop = (
            counters["pcSearch"][0]["pointProgress"]
            + counters["pcSearch"][1]["pointProgress"]
        )
        targetDesktop = (
            counters["pcSearch"][0]["pointProgressMax"]
            + counters["pcSearch"][1]["pointProgressMax"]
        )
        if targetDesktop in [33, 102]:
            # Level 1 or 2 EU
            searchPoints = 3
        elif targetDesktop == 55 or targetDesktop >= 170:
            # Level 1 or 2 US
            searchPoints = 5
        remainingDesktop = int((targetDesktop - progressDesktop) / searchPoints)
        remainingMobile = 0
        if dashboard["userStatus"]["levelInfo"]["activeLevel"] != "Level1":
            progressMobile = counters["mobileSearch"][0]["pointProgress"]
            targetMobile = counters["mobileSearch"][0]["pointProgressMax"]
            remainingMobile = int((targetMobile - progressMobile) / searchPoints)
        return remainingDesktop, remainingMobile


def prRed(prt):
    print(f"\033[91m{prt}\033[00m")


def prGreen(prt):
    print(f"\033[92m{prt}\033[00m")


def prPurple(prt):
    print(f"\033[95m{prt}\033[00m")


def prYellow(prt):
    print(f"\033[93m{prt}\033[00m")


def format_number(number, num_decimals=2):
    """
    Format a number as a string including thousands separators.

    :param number: The number to format (a number like an :class:`int`,
                   :class:`long` or :class:`float`).
    :param num_decimals: The number of decimals to render (2 by default). If no
                         decimal places are required to represent the number
                         they will be omitted regardless of this argument.
    :returns: The formatted number (a string).

    This function is intended to make it easier to recognize the order of size
    of the number being formatted.

    Here's an example:

    >>> print(format_number(6000000))
    6,000,000
    > print(format_number(6000000000.42))
    6,000,000,000.42
    > print(format_number(6000000000.42, num_decimals=0))
    6,000,000,000
    """
    integer_part, _, decimal_part = str(float(number)).partition(".")
    negative_sign = integer_part.startswith("-")
    reversed_digits = "".join(reversed(integer_part.lstrip("-")))
    parts = []
    while reversed_digits:
        parts.append(reversed_digits[:3])
        reversed_digits = reversed_digits[3:]
    formatted_number = "".join(reversed(",".join(parts)))
    if decimals_to_add := decimal_part[:num_decimals].rstrip("0"):
        formatted_number += f".{decimals_to_add}"
    if negative_sign:
        formatted_number = f"-{formatted_number}"
    return formatted_number
