import random
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def create_driver():
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    ]
    user_agent = random.choice(user_agent_list)

    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument("--no-sandbox")
    browser_options.add_argument("--headless")
    browser_options.add_argument("start-maximized")
    browser_options.add_argument("window-size=1900,1080")
    browser_options.add_argument("disable-gpu")
    browser_options.add_argument("--disable-software-rasterizer")
    browser_options.add_argument("--disable-dev-shm-usage")
    browser_options.add_argument(f"user-agent={user_agent}")

    service = Service(log_path="test.log")

    driver = webdriver.Chrome(service=service, options=browser_options)

    return driver


from datetime import datetime


def parse_data(driver, url):
    driver.get(url)

    data_table = driver.find_element(By.CLASS_NAME, "calendar__table")
    value_list = []
    current_date = None

    for row in data_table.find_elements(By.TAG_NAME, "tr"):
        row_data = list(
            filter(None, [td.text for td in row.find_elements(By.TAG_NAME, "td")])
        )
        if not row_data:
            continue

        # Handle date entries
        if "\n" in row_data[0]:
            current_date = row_data[0].replace("\n", " - ")
            continue

        # Handle entries missing a time value
        if len(row_data) > 0 and not row_data[0][0].isdigit():
            row_data.insert(0, "")  # Insert empty time value for consistency

        value_list.append([current_date] + row_data)

    return value_list


driver = create_driver()
url = "https://www.forexfactory.com/calendar?day=mar20.2025"

value_list = parse_data(driver=driver, url=url)


# Display formatted output
for value in value_list:
    print(f"Date: {value[0]}")
    print(
        f"  Time: {value[1]} | Currency: {value[2]} | Event: {value[3]} | Actual: {value[4] if len(value) > 4 else 'N/A'} | Forecast: {value[5] if len(value) > 5 else 'N/A'} | Previous: {value[6] if len(value) > 6 else 'N/A'}"
    )
