import re
from selenium import webdriver


class TransferMarkt:
    def __init__(self, executable_path: str = "chromedriver"):
        """
        Controls the ChromeDriver and allows you to drive the browser.
        You will need to download the ChromeDriver executable from http://chromedriver.storage.googleapis.com/index.html

        Parameters:
        executable_path : Path to the ChromeDriver
        """
        self.driver = webdriver.Chrome(executable_path)
        self.driver.implicitly_wait(5)

    def get_market_value(self, url: str):
        """
        Loads a page of market value.

        Parameters:
        url: The url of the page of market value.
        """
        self.driver.get(url)
        clubs = self.driver.find_elements_by_class_name(
            "vereinprofil_tooltip.tooltipstered"
        )
        clubs = [club.get_attribute("href") for club in clubs]
        clubs = [re.findall(r"(\d+)", club)[0] for club in clubs]

        mvs = self.driver.find_elements_by_class_name("rechts.hauptlink")
        mvs = [mv.text.strip() for mv in mvs]
        # TODO str to int

    def quit(self):
        self.driver.quit()


def test():
    driver = TransferMarkt("/Users/tanjt107/Documents/chromedriver")
    driver.get_market_value(
        "https://www.transfermarkt.com/hong-kong-first-division/marktwerteverein/wettbewerb/HK2L"
    )
    driver.quit()


if __name__ == "__main__":
    test()
