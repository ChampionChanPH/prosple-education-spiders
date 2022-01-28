# -*- coding: utf-8 -*-
# by Christian Anasco
# courses on page 1 can be scraped, having issues getting to next pages

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


class TaqSpiderSpider(scrapy.Spider):
    name = 'taq_spider'
    start_urls = ['https://tafeqld.edu.au/search-results.html?study_area_group=Engineering']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.course_parse, args={"wait": 20})

    def course_parse(self, response):
        courses = response.xpath("//div[@class='tq-search-result__title']/a/@href").getall()

        next_page = response.xpath("//a[@class='page-link']/@href").getall()

        print(courses)
        print(next_page)
