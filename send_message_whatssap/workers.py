import json
import sys
import time

import pymongo
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from send_message_whatssap.open_browser import driver

from helpers.io_helpers import *
from selenium.webdriver.common.by import By


def contact_save(number):
    database = "contact"
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["whatsapp"]
    mycol = mydb[database]
    n = list(mycol.find({"phone": number}))
    if len(n) != 0:
        result = {"exist": True, "name": n[0]["name_contact"]}
    else:
        result = {"exist": False}
    return result


class SendMessageWorker():
    def serve_request(self, request_body):
        request = json.loads(request_body.decode("utf-8"))
        data = request["data"]

        try:
            if data is None:
                data = {}

            results = self.business_flow(data)

            response = create_success_response(tracking_code=request["tracking_code"],
                                               method_type=request["method"],
                                               response=results,

                                               broker_type=request["broker_type"],
                                               source=request["source"],
                                               )
        except:
            response = create_error_response(status=401, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Exception",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             )

        return json.dumps(response)

    def business_flow(self, data):

        if contact_save(data["number"])["exist"]:
            contact = contact_save(data["number"])["name"]
            # options: Options = webdriver.ChromeOptions()
            # options.add_argument(r'--user-data-dir=/home/maryam/.config/google-chrome')
            # driver = webdriver.Chrome(
            #     "./send_message_whatssap/chromedriver4",
            #     options=options
            # )
            # driver.get("https://web.whatsapp.com")
            while True:
                try:
                    input_box_search = driver.find_element(By.CLASS_NAME, "_13NKt")
                    input_box_search.click()
                    input_box_search.clear()
                    input_box_search.click()
                    input_box_search.send_keys(contact)
                    selected_contact = driver.find_element(By.XPATH, '//span[@title="{}"]'.format(contact))
                    selected_contact.click()
                    input_box = driver.find_element(By.CLASS_NAME, "_1LbR4")
                    input_box.click()
                    message = data["message"]
                    input_box.send_keys(message)
                    driver.find_element(By.CLASS_NAME, "_1Ae7k").click()
                    break
                except:
                    pass

            results = {"send": True}

        else:
            ports = int(sys.argv[1])
            options: Options = webdriver.ChromeOptions()
            # options.add_argument('headless')
            if ports == 1:
                options.add_argument(r'--user-data-dir=/home/maryam/.config/google-chrome-unstable')
            if ports == 2:
                options.add_argument(r'--user-data-dir=/home/maryam/.config/google-chrome (another copy)')
            if ports == 3:
                options.add_argument(r'--user-data-dir=/home/maryam/.config/google-chrome (copy)')
            browser = webdriver.Chrome(
                "./send_message_whatssap/chromedriver{}".format(ports),
                options=options
            )
            browser.get("https://web.whatsapp.com/send?phone={},&text={}".format(data["number"], data["message"]))
            while True:
                try:
                    button = browser.find_element(By.CLASS_NAME, "_1Ae7k")
                    button.click()
                    break
                except:
                    time.sleep(0.00001)
                    pass
            time.sleep(2)
            browser.close()
            results = {"send": True}
        return results
