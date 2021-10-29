# -*- coding: utf-8 -*-
# by Christian Anasco
# spider used to grab CSF course data

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
from pandas import DataFrame, Series
from tqdm import tqdm

URL = 'https://csf.edu.au/courses/'

options = Options()
# options.headless = True
driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(10)

# closeBtn = driver.find_element(By.XPATH, "//a[@class='LiBGaQAEBxZn48tqybV_r']")
# if closeBtn:
#     closeBtn.click()
#     time.sleep(1)

images = driver.find_elements(By.XPATH, "//a[@tabindex = '-1' and @class='pushed']")
for item in images:
    url = item.get_attribute('href')
    print(url)
#
# while True:
#     try:
#         btn = driver.find_element(By.XPATH, "//button[@class='_2srtpdMNJdXb549RYlV0fC']")
#         btn.click()
#         time.sleep(2)
#         box = driver.find_elements(By.XPATH, "//div[@class='_157tdY99JCRU_Qa5y4dl6U']")
#         if len(box) >= TOTAL_EMPLOYERS:
#             break
#     except NoSuchElementException:
#         break
#
# company_holder = []
#
# box = driver.find_elements(By.XPATH, "//div[@class='_157tdY99JCRU_Qa5y4dl6U']")
#
# for item in tqdm(box, desc='Getting data: '):
#     name = item.find_element(By.XPATH, ".//a[@data-automation='CompanySearchResult']/span").text
#     profile_page = item.find_element(By.XPATH, ".//a[@data-automation='CompanySearchResult']").get_attribute('href')
#     rating = item.find_element(By.XPATH, ".//div[@class='_1wZg4X_PMV4mxozQYM7ILi']/span").text
#     rating_count = item.find_element(By.XPATH, ".//a[@class='_1OOiQayttuMEAr5uewwVMY']/span").text
#     company_holder.append([name, profile_page, rating, rating_count])
#
# docs = DataFrame(columns=[])
# for company in tqdm(company_holder, desc='Adding to documents: '):
#     series_obj = Series(company)
#     docs = docs.append(series_obj, ignore_index=True)
#
# docs.to_csv('jobstreet_employers.csv', ",", index=False,
#             header=['Company Name', 'Profile Link', 'Rating', 'Rating Count'])

driver.quit()
