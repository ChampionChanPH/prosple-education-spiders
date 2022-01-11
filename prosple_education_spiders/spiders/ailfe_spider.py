# -*- coding: utf-8 -*-
# by Christian Anasco
import re

from ..standard_libs import *
from ..scratch_file import strip_tags


def research_coursework(course_item):
    if re.search("research", course_item["courseName"], re.I):
        return "12"
    else:
        return "11"


def bachelor_honours(course_item):
    if re.search("honours", course_item["courseName"], re.I):
        return "3"
    else:
        return "2"


def get_total(field_to_use, field_to_update, course_item):
    if "durationMinFull" in course_item and "teachingPeriod" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])
        if course_item["teachingPeriod"] == 12:
            if float(course_item["durationMinFull"]) < 12:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"]) \
                                               / 12
        if course_item["teachingPeriod"] == 52:
            if float(course_item["durationMinFull"]) < 52:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"]) \
                                               / 52


class AilfeSpiderSpider(scrapy.Spider):
    name = 'ailfe_spider'
    start_urls = ['https://www.ailfe.wa.edu.au/courses']
    institution = "Australian Institute of Language and Further Education (AILFE)"
    uidPrefix = "AU-AILFE-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    months = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"
    }

    campuses = {
        "Perth Campus": "83028",
        "Sydney Campus": "83029",
        "Brisbane Campus": "83027"
    }

    teaching_periods = {
        "year": 1,
        "semester": 2,
        "trimester": 3,
        "quarter": 4,
        "month": 12,
        "week": 52,
        "day": 365
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//div[@data-testid='mesh-container-content']/div//li//a/@href").getall()

        for item in courses:
            if re.search("ailfe.wa.edu.au", item):
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//div[contains(@id, 'comp-')][2]//h2[@class='font_2']//a/text()").get()
        if not course_name:
            course_name = response.xpath("//div[contains(@id, 'comp-')][2]//h2[@class='font_2']//span/text()").get()
        if course_name:
            if re.search("[A-Z0-9]+[A-Z0-9]+ ", course_name):
                course_code, course_name = re.split("\\s", strip_tags(course_name), maxsplit=1)
                course_item.set_course_name(strip_tags(course_name), self.uidPrefix)
                course_item["courseCode"] = strip_tags(course_code)
            else:
                course_item.set_course_name(strip_tags(course_name), self.uidPrefix)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        yield course_item
