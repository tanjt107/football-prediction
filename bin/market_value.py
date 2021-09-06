import json
import os
import time
from selenium import webdriver
from param import MARKET_VALUE_FOLDER_PATH, MARKET_VALUE_PARAM_PATH, WEBDRIVER_PATH

def main(url: str) -> dict:
    result = dict()
    driver.get(url)
    time.sleep(5)
    teams = driver.find_elements_by_class_name("hauptlink.no-border-links")
    values = driver.find_elements_by_class_name("rechts.hauptlink")
    for team, value in zip(teams, values):
        result[
            lookup.get(team.text.strip(), team.text.strip())
            ] =  value.text.strip()
    return result

if __name__ == '__main__':
    with open(MARKET_VALUE_PARAM_PATH, 'r') as f:
        param = json.load(f)

    lookup = param['lookup']
    driver = webdriver.Chrome(WEBDRIVER_PATH)

    for league, url in list(param['league'].items()):
        result = main(url)

        with open(os.path.join(MARKET_VALUE_FOLDER_PATH, f'{league}.json'), 'w') as f:
            json.dump(result, f, indent=4)

    driver.quit()