import random
from fastapi import APIRouter, HTTPException, Query
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

router = APIRouter()


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

        if "\n" in row_data[0]:
            current_date = row_data[0].replace("\n", " - ")
            continue

        if len(row_data) > 0 and not row_data[0][0].isdigit():
            row_data.insert(0, "")

        value_list.append([current_date] + row_data)

    driver.quit()
    return value_list


@router.get("/forex-data")
async def get_forex_data(
    day: int = Query(..., ge=1, le=31), month: str = Query(...), year: int = Query(...)
):
    try:
        month = month.lower()[:3]  # Ensure month is in short format (e.g., 'mar')
        url = f"https://www.forexfactory.com/calendar?day={month}{day}.{year}"
        driver = create_driver()
        value_list = parse_data(driver, url)

        return {"data": value_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
