# -*- coding: utf-8 -*-
# by Christian Anasco
# this is used to get the course links for ARA

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import os
import re
from pandas import DataFrame, Series
from tqdm import tqdm

URL = 'https://www.ara.ac.nz/course-search-page'

options = Options()
# options.headless = True
driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(2)

course_holder = []

while True:
    try:
        courses = driver.find_elements(By.XPATH, "//div[contains(@class, 'courseSearchContainer-item')]")
        for item in courses:
            link = item.find_element(By.XPATH, ".//a[@data-blk='CourseSearchResultItemBlock']").get_attribute('href')
            course_holder.append(link)
        next_button = driver.find_element(By.XPATH, "//li[@class='paginationjs-next J-paginationjs-next']")
        next_button.click()
        time.sleep(20)
    except NoSuchElementException:
        break

docs = DataFrame(columns=[])
for course in tqdm(course_holder, desc='Adding to documents: '):
    series_obj = Series(course)
    docs = docs.append(series_obj, ignore_index=True)

file_directory = os.getcwd()
file_path = re.sub('selenium_spiders', r'resources\\ara_courses.csv', file_directory)
docs.to_csv(file_path, ",", index=False, header=['Course Link'])

driver.quit()
