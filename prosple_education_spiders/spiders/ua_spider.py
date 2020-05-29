# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class UaSpiderSpider(scrapy.Spider):
    name = 'ua_spider'
    allowed_domains = ['www.auckland.ac.nz']
    start_urls = ['https://www.auckland.ac.nz/en/study/study-options/find-a-study-option.html']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Auckland"
    uidPrefix = "NZ-UA-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "foundation certificate": "4"
    }

    def parse(self, response):
        courses = response.xpath("//ul[preceding-sibling::div/div/h3[contains(text(), 'Programmes')]]/li")
        for li in courses:
            course = li.css("a::attr(href)").get()
            name = li.css("p::attr(data-programme-name)").get()
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse, meta={"name": name})

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        # name = response.css("h1::text").get()
        name = response.meta["name"]
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees, ["and"])

        overview = response.xpath("//div[preceding-sibling::div/h2/text()='Programme overview']/p/text()").getall()
        if overview:
            course_item["overview"] = "\n".join(overview)
            course_item.set_summary(" ".join(overview))
        # if "flag" in course_item:
        yield course_item
