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

class AutSpiderSpider(scrapy.Spider):
    name = 'aut_spider'
    # allowed_domains = ['https://www.aut.ac.nz/s/search.html?query=']
    start_urls = ['https://www.aut.ac.nz/s/search.html?query=&collection=aut-ac-nz-meta-dev&sitetheme=orange&f.Tabs%7CT=Course&tab=Course&num_ranks=1000&form=simple&&_=1592491274316&start_rank=1']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Auckland University of Technology"
    uidPrefix = "NZ-AUT-"

    degrees = {
        # "master": "11",
        # "bachelor": bachelor,
        # "postgraduate certificate": "7",
        # "postgraduate diploma": "8",
        # "artist diploma": "5",
        # "foundation certificate": "4"
    }

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.catalog_page, args={'wait': 3})

    def catalog_page(self, response):
        courses = response.css("div.search-result")