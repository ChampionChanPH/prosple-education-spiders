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

class UwSpiderSpider(scrapy.Spider):
    name = 'uw_spider'
    # allowed_domains = ['https://www.waikato.ac.nz/study/qualifications']
    start_urls = ['https://www.waikato.ac.nz/study/qualifications']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "https://www.waikato.ac.nz/study/qualifications/conjoint-degree",
        "https://www.waikato.ac.nz/study/qualifications/individual-paper-credit",
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "University of Waikato"
    uidPrefix = "NZ-UW-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "international diploma": "5",
        # "professional master": "11",
        # "diploma for graduates": "8"
    }

    campus_map = {
        "Tauranga": "49145",
        "Hamilton": "49144"
    }

    holder = []

    def parse(self, response):
        course_cards = response.css("li.course-finder__result")
        for card in course_cards:
            summary = card.css("div.course-finder__result-description p").getall()
            if summary:
                summary = re.sub("<.*?>", "", summary[-1])
            name = card.css("h3::text").get()
            code = card.css("li.course-finder__result-code::text").get()
            course = card.css("a.course-finder__result-title::attr(href)").get()
            course = response.urljoin(course)
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse, meta={"summary": summary, "name": name, "code": code})

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.meta["name"]
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        code = response.meta["code"]
        if code:
            course_item["courseCode"] = cleanspace(code)

        summary = response.meta["summary"]
        if summary:
            course_item.set_summary(cleanspace(summary))

        # if response.request.url == "https://www.waikato.ac.nz/study/qualifications/certificate":
        #     course_item["degreeType"] = "4"
        #     course_item["courseLevel"] = "1"
        #     course_item["rawStudyfield"] = "certificate generic"
        #     course_item["specificStudyField"] = "Certificate"
        # else:
        course_item.set_sf_dt(self.degrees, ["&", "/"])

        if "flag" in course_item:
            yield course_item



