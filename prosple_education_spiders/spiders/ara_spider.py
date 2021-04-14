# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *
import requests
# import pkgutil


MAIN_URL = 'https://ara-test.apigee.net/productdata/api/v1/'
api_key = 'jGhux5kJNO7AcRlXi5ZYMWjohBIjGwE7'

payload = {
    'x-api-key': api_key,
}

courses = requests.get(MAIN_URL + 'programme', params=payload)
courses = courses.json()


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


# course_data = pkgutil.get_data("prosple_education_spiders", "resources/ara_courses - TEST.csv").decode("utf-8")
# course_data = re.split('\r\n', course_data)


class AraSpiderSpider(scrapy.Spider):
    name = 'ara_spider'
    start_urls = ['https://www.ara.ac.nz/course-search-page']
    institution = "Ara Institute of Canterbury"
    uidPrefix = "NZ-ARA-"

    campuses = {
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "undergraduate certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        for item in courses:
            course = requests.get(MAIN_URL + 'programme/' + item, params=payload)
            course = course.json()

            course_item = Course()

            course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")

            if 'url' in course:
                course_item["sourceURL"] = course['url']

            course_item["published"] = 1
            course_item["institution"] = self.institution

            if 'productTitle' in course:
                course_item.set_course_name(course['productTitle'].strip(), self.uidPrefix)

            if 'longDescription' in course:
                course_item['overview'] = strip_tags(course['longDescription'], remove_all_tags=False,
                                                     remove_hyperlinks=True)

            if 'shortDescription' in course:
                course_item.set_summary(strip_tags(course['shortDescription']))
            elif 'longDescription' in course:
                course_item.set_summary(strip_tags(course['longDescription']))

            if 'sdrCode' in course:
                course_item['courseCode'] = course['sdrCode']

            if 'fees' in course and '2021' in course['fees'] and 'domesticTuitionMaxFee' in course['fees']['2021']:
                course_item['domesticFeeTotal'] = course['fees']['2021']['domesticTuitionMaxFee']

            if 'fees' in course and '2021' in course['fees'] and 'internationalTuitionFee' in course['fees']['2021']:
                course_item['internationalFeeTotal'] = course['fees']['2021']['internationalTuitionFee']

            if 'studyPathWay' in course:
                course_item['careerPathways'] = strip_tags(course['studyPathWay'], remove_all_tags=False,
                                                           remove_hyperlinks=True)

            if 'outcome' in course:
                course_item['careerPathways'] = strip_tags(course['outcome'], remove_all_tags=False,
                                                           remove_hyperlinks=True)

            if 'duration' in course:
                duration_full = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
                    course['duration'], re.I | re.M | re.DOTALL)
                duration_part = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
                    course['duration'], re.I | re.M | re.DOTALL)
                if not duration_full and duration_part:
                    self.get_period(duration_part[0][1].lower(), course_item)
                if duration_full:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if duration_part:
                    if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                        course_item["durationMinPart"] = float(duration_part[0][0])
                    else:
                        course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                         / self.teaching_periods[duration_part[0][1].lower()]
                if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                    duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                               course['duration'], re.I | re.M | re.DOTALL)
                    if duration_full:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                        # if len(duration_full) == 1:
                        #     course_item["durationMinFull"] = float(duration_full[0][0])
                        #     self.get_period(duration_full[0][1].lower(), course_item)
                        # if len(duration_full) == 2:
                        #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        #     self.get_period(duration_full[1][1].lower(), course_item)

            yield course_item
