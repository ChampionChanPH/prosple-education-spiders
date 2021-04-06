# -*- coding: utf-8 -*-
# by Christian Anasco
# spider used to grab some data from linkedin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import re
import os
from pandas import DataFrame, Series
from tqdm import tqdm


class InfiniteScroll(object):
    def __init__(self, last):
        self.last = last

    def __call__(self, _driver):
        new = _driver.execute_script('return document.body.scrollHeight')
        if new > self.last:
            return new
        else:
            return False


URL = 'https://www.linkedin.com/jobs/search/?currentJobId=2439310394&keywords=graduate%20program&originalSubdomain=ph'

options = Options()
# options.headless = True
driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(10)

last_height = driver.execute_script('return document.body.scrollHeight')
flag = 1

while flag == 1:
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')

    try:
        wait = WebDriverWait(driver, 10)

        new_height = wait.until(InfiniteScroll(last_height))
        last_height = new_height
    except (NoSuchElementException, TimeoutException):
        print("Infinite scrolling done...")
        flag = 0

company_holder = []

box = driver.find_elements(By.XPATH, "//li[contains(@class, 'job-result-card')]")

for item in box:
    job_name = item.find_element(By.XPATH, ".//h3[contains(@class, 'result-card__title')]").text
    company_name = item.find_element(By.XPATH, ".//h4[contains(@class, 'result-card__subtitle')]").text
    try:
        company_profile = item.find_element(By.XPATH, ".//h4[contains(@class, 'result-card__subtitle')]/a")\
            .get_attribute('href')
        if company_profile:
            company_profile = re.sub('\?trk.+', '', company_profile, re.DOTALL)
    except NoSuchElementException:
        company_profile = None
    company_holder.append([job_name, company_name, company_profile])

docs = DataFrame(columns=[])
for company in tqdm(company_holder, desc='Adding to documents: '):
    series_obj = Series(company)
    docs = docs.append(series_obj, ignore_index=True)

file_directory = os.getcwd()
file_path = re.sub('selenium_spiders', r'resources\\linkedin_jobs.csv', file_directory)
docs.to_csv(file_path, ",", index=False,
            header=['Application Name', 'Company Name', 'Company Profile'])

driver.quit()
