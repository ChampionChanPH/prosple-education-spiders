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
    if "durationMinFull" in course_item and "teachingPeriod" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class CucSpiderSpider(scrapy.Spider):
    name = 'cuc_spider'
    start_urls = ['http://a/']
    institution = 'North Metropolitan TAFE'
    uidPrefix = 'AU-NOM-'

    campuses = {
        "Balga": "59264",
        "Clarkson": "59265",
        "East Perth": "59266",
        "Joondalup (Kendrew Crescent)": "59267",
        "Joondalup (McLarty Avenue)": "59268",
        "Leederville": "59269",
        "Midland": "59270",
        "Mount Lawley": "59271",
        "Nedlands (Oral Health Centre)": "59272",
        "Perth": "59273",
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
        "foundation certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
        'postgraduate diploma': '8',
        'postgraduate certificate': '7',
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

    term = {
        'Semester 1': '02',
        'Semester 2': '07',
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.css(
            "div.cmp-spotlight__content a::attr(href)").getall()

        for item in categories:
            if re.search("masters-qualifying-program", item):
                yield response.follow(item, callback=self.course_parse)
            else:
                yield response.follow(item, callback=self.category_parse)

    def category_parse(self, response):
        courses = response.xpath(
            "//a[span[@class='cmp-button__text'][text()='View more' or text()='View course']]/@href").getall()
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              "and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
