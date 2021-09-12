import json
import os
import time
from param import CHROMEDRIVER_PATH, MARKET_VALUE_URL_LIST, PARENT_DIRECTORY
from selenium import webdriver

def main(url: str) -> dict:
    result = dict()
    driver.get(url)
    time.sleep(5)
    teams = driver.find_elements_by_class_name("hauptlink.no-border-links")
    values = driver.find_elements_by_class_name("rechts.hauptlink")
    for team, value in zip(teams, values):
        result[team.text.strip()] =  value.text.strip()
    return result

if __name__ == '__main__':
    driver = webdriver.Chrome(CHROMEDRIVER_PATH)

    for league, url in MARKET_VALUE_URL_LIST.items():
        result = main(url)

        with open(os.path.join(PARENT_DIRECTORY, "data/market-value", f'{league}.json'), 'w') as f:
            json.dump(result, f, indent=4)

    driver.quit()