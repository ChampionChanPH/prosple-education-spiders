# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

class AcnSpiderSpider(scrapy.Spider):
    name = 'acn_spider'
    # allowed_domains = ['https://www.acn.edu.au/education/postgraduate-courses']
    start_urls = ['https://www.acn.edu.au/education/postgraduate-courses/']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Australian College of Nursing (ACN)"
    uidPrefix = "AU-ACN-"

    download_delay = 5

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.postgrad_catalog, args={'wait': 10})

    def postgrad_catalog(self, response):
        courses = response.css(".standard-arrow a::attr(href)").getall()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(course, callback=self.course_parse, args={'wait': 10}, meta={"url":course})

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta["url"]

        course_item.set_course_name(response.css("div.uvc-sub-heading::text").get(), self.uidPrefix)

        overview = response.xpath("//div[preceding-sibling::h2/text()='Course overview'][position()=2]/div/p/text()").getall()
        # if overview:
        #     course_item["overview"] = "<br>".join(overview)

        course_item.set_sf_dt()


        yield course_item