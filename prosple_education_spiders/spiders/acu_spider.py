# -*- coding: utf-8 -*-
# by Christian Anasco

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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


class AcuSpiderSpider(scrapy.Spider):
    name = 'acu_spider'
    allowed_domains = ['www.acu.edu.au', 'acu.edu.au']
    start_urls = [
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Undergraduate',
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Postgraduate',
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Research',
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Other'
    ]
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    courses = []
    institution = "The University of Queensland (UQ)"
    uidPrefix = "AU-UOQ-"

    campuses = {
        "Teaching Hospitals": "715",
        "Ipswich": "716",
        "Brisbane": "718",
        "Pharmacy Aust Cntr Excellence": "717",
        "Herston": "714",
        "Gatton": "713",
        "St Lucia": "711",
        "External": "712"
    }

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
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.main_parse, args={'wait': 20})

    def main_parse(self, response):
        courses = response.xpath("//section[contains(@class, 'search-results-scholarships')]//input["
                                 "@type='hidden']/@value").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        if "courseName" in course_item:
            if re.search("postgraduate", course_item["courseName"], re.I):
                course_item["courseLevel"] = "Postgraduate"
                course_item["canonicalGroup"] = "PostgradAustralia"
                course_item["group"] = 4

        yield course_item
