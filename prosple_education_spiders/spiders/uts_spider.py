# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def master(course_item):
    if "research" in course_item["courseName"].lower():
        return "12"

    else:
        return "11"

class UtsSpiderSpider(scrapy.Spider):
    name = 'uts_spider'
    # allowed_domains = ['https://www.uts.edu.au/future-students']
    start_urls = ['https://www.uts.edu.au/future-students/']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Technology, Sydney (UTS)"
    uidPrefix = "AU-UTS-"

    degrees = {
        "master": master,
    }

    def parse(self, response):
        categories = response.css("nav.content-menu--course-areas a::attr(href)").extract()
        for category in categories:
            yield response.follow(response.urljoin(category), callback=self.category_page)

    def category_page(self, response):
        sub_categories = response.css(".view-study-areas a::attr(href)").extract()
        for sub_category in sub_categories:
            yield response.follow(response.urljoin(sub_category), callback=self.sub_category_page)

    def sub_category_page(self, response):
        courses = response.css(".views-field a::attr(href)").extract()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(response.urljoin(course), callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_item["courseName"] = response.css("h1::text").extract_first()
        course_item["uid"] = self.uidPrefix + course_item["courseName"]

        course_item.set_sf_dt(self.degrees)
        yield course_item

