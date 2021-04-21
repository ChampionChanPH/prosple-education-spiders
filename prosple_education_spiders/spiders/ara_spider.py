# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *
import requests
# import pkgutil


TEST_URL = 'https://ara-test.apigee.net/productdata/api/v1/'
MAIN_URL = 'https://ara-prod.apigee.net/productdata/api/v1/'
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
        "new zealand diploma": "5",
        "new zealand certificate": "4",
        'n.z. certificate': '4',
        'n.z. cert.': '4',
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

            if 'url' in course and course['url']:
                course_item["sourceURL"] = course['url']

            course_item["published"] = 1
            course_item["institution"] = self.institution

            name = None
            if 'productTitle' in course and course['productTitle']:
                course_name = course['productTitle']
                name = course_name[:]
                if re.search('\(.*(master|bachelor|diploma)', course_name, flags=re.I | re.M | re.DOTALL):
                    course_name = re.sub('\(.*(master|bachelor|diploma).*', '', course_name,
                                         flags=re.I | re.M | re.DOTALL)
                if course_name:
                    course_item['courseName'] = course_name.strip()

            if 'longDescription' in course and course['longDescription']:
                course_item['overview'] = strip_tags(course['longDescription'], remove_all_tags=False,
                                                     remove_hyperlinks=True)

            if 'shortDescription' in course and course['shortDescription']:
                course_item.set_summary(strip_tags(course['shortDescription']))
            elif 'longDescription' in course and course['longDescription']:
                course_item.set_summary(strip_tags(course['longDescription']))

            if 'uiCode' in course and course['uiCode']:
                course_item['courseCode'] = course['uiCode']

            if 'outcome' in course and course['outcome']:
                course_item['careerPathways'] = strip_tags(course['outcome'], remove_all_tags=False,
                                                           remove_hyperlinks=True)

            if 'duration' in course and course['duration']:
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

            if 'fees' in course and '2021' in course['fees']:
                if 'domesticTuitionMaxFee' in course['fees']['2021'] and \
                        course['fees']['2021']['domesticTuitionMaxFee']:
                    course_item['domesticFeeAnnual'] = course['fees']['2021']['domesticTuitionMaxFee']
                    get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

            if 'fees' in course and '2021' in course['fees']:
                if 'internationalTuitionFee' in course['fees']['2021'] and \
                        course['fees']['2021']['internationalTuitionFee']:
                    course_item['internationalFeeAnnual'] = course['fees']['2021']['internationalTuitionFee']
                    get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

            course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

            if 'teachingPeriod' in course_item and 'durationMinFull' in course_item and \
                    ((course_item['teachingPeriod'] == 1 and course_item['durationMinFull'] <= 0.5) or
                     (course_item['teachingPeriod'] == 12 and course_item['durationMinFull'] <= 6)):
                course_item['degreeType'] = 'Short course or microcredential'

            course_item['group'] = 2
            course_item['canonicalGroup'] = 'GradNewZealand'

            if name:
                course_item.set_course_name(name.strip(), self.uidPrefix)

            if 'uid' in course_item and 'courseCode' in course_item:
                course_item['uid'] += '-' + course_item['courseCode']

            yield course_item
