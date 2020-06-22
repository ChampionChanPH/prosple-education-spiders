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

class CduSpiderSpider(scrapy.Spider):
    name = 'cdu_spider'
    # allowed_domains = ['https://www.cdu.edu.au/course-search']
    start_urls = ['https://www.cdu.edu.au/course-search/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Charles Darwin University (CDU)"
    uidPrefix = "AU-CDU-"

    degrees = {
        "master": "11",
        "master by research": "12",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "bachelor": bachelor,
        # "postgraduate certificate": "7",
        # "postgraduate diploma": "8",
        # "artist diploma": "5",
        # "foundation certificate": "4"
    }

    def parse(self, response):
        course_rows = response.css(".js-shortlist div.fable__row")

        for row in course_rows:
            course = row.css("a::attr(href)").get()
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse)

        next_page = response.css("a[rel='next']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            name = cleanspace(name)

            if re.findall("\d", name.split(" ")[0]):
                course_item["courseCode"] = name.split(" ")[0]
                name = re.sub("^.*?\s", "", name)


            course_item.set_course_name(name, self.uidPrefix)
            course_item.set_sf_dt(self.degrees)

        if "flag" in course_item:
            yield course_item
