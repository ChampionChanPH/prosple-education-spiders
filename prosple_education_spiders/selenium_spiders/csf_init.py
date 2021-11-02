# -*- coding: utf-8 -*-
# by Christian Anasco
# spider used to grab CSF course data

from pandas import DataFrame, Series
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import re
import os

URL = 'https://csf.edu.au/courses/'

options = Options()
# options.headless = True
driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(2)

images = driver.find_elements(By.XPATH, "//a[@tabindex = '-1' and @class='pushed']")
url_holder = []
course_holder = []
for item in images:
    URL = item.get_attribute('href')
    url_holder.append(URL)
for url in url_holder:
    driver.get(url)
    time.sleep(2)
    single_holder = [url, ]
    try:
        name = driver.find_element(By.XPATH, "//h1[contains(@class, 'header-title')]/span").text
        single_holder.append(name)
    except NoSuchElementException:
        name = None
        single_holder.append(name)
    try:
        cricos = driver.find_element(By.XPATH, "//p[contains(text(), 'CRICOS Course Code')]").text
        single_holder.append(cricos)
    except NoSuchElementException:
        cricos = None
        single_holder.append(cricos)
    try:
        overview = driver.find_elements(By.XPATH, "//section//div[@class='uncode_text_column']/p")
        holder = []
        for item in overview:
            html = item.get_attribute("outerHTML")
            if not re.search("iframe", html) and not re.search("CRICOS Course Code", html):
                holder.append(html)
        overview = ''.join(holder)
        single_holder.append(overview)
    except NoSuchElementException:
        overview = []
        single_holder.append(overview)
    try:
        duration = driver.find_element(By.XPATH, "//h4[span/text()='Duration' or span/text()='Course "
                                                 "Duration']/following-sibling::*/p").text
        single_holder.append(duration)
    except NoSuchElementException:
        duration = None
        single_holder.append(duration)
    try:
        delivery = driver.find_element(By.XPATH, "//h4[span/text()='Delivery Mode']/following-sibling::*/p").text
        single_holder.append(delivery)
    except NoSuchElementException:
        delivery = None
        single_holder.append(delivery)
    try:
        career = driver.find_element(By.XPATH, "//h4[span/text()='Career Prospects']/following-sibling::*/p") \
            .get_attribute("outerHTML")
        single_holder.append(career)
    except NoSuchElementException:
        career = None
        single_holder.append(career)
    try:
        location = driver.find_element(By.XPATH, "//h4[span/text()='Location']/following-sibling::*/p").text
        single_holder.append(location)
    except NoSuchElementException:
        location = None
        single_holder.append(location)
    course_holder.append(single_holder[:])

docs = DataFrame(columns=[])
for course in tqdm(course_holder, desc='Adding to documents: '):
    series_obj = Series(course)
    docs = docs.append(series_obj, ignore_index=True)

file_directory = os.getcwd()
file_path = re.sub('selenium_spiders', r'resources\\csf_courses.csv', file_directory)
docs.to_csv(file_path, ",", index=False,
            header=['URL', 'Name', 'CRICOS', 'Overview', 'Duration', 'Delivery', 'Career', 'Location'])

driver.quit()
