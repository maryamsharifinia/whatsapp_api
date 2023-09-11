from selenium.webdriver.chrome.options import Options
from selenium import webdriver
try:
    options: Options = webdriver.ChromeOptions()
    options.add_argument(r'--user-data-dir=/home/maryam/.config/google-chrome/test')
    driver = webdriver.Chrome(
        "./chromedriver4",
        options=options
    )
    driver.get("https://web.whatsapp.com")
except:
    pass