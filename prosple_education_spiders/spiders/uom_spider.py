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


class UomSpiderSpider(scrapy.Spider):
    name = 'uom_spider'
    allowed_domains = ['study.unimelb.edu.au', 'unimelb.edu.au']
    start_urls = ['https://study.unimelb.edu.au/find/']
    banned_urls = []
    institution = "University of Melbourne"
    uidPrefix = "AU-UOM-"

    campuses = {
        "Sydney": "765",
        "Armidale": "764"
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

    def parse(self, response):
        categories = response.xpath("//div[@data-test='interest-list']//a[@data-test='interest-item']/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//ul[@data-test='course-list']//a/@href").getall()

        for item in courses:
            if item not in self.banned_urls and \
                    not re.search("/major/", item):
                yield response.follow(item, callback=self.sub_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@data-test='header-course-title']/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        yield course_item