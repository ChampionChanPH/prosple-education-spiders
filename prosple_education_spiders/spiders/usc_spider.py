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


def doctor(course_item):
    if course_item["courseLevel"] == "Undergraduate":
        return "2"
    else:
        return "6"


class UscSpiderSpider(scrapy.Spider):
    name = 'usc_spider'
    # allowed_domains = ['https://www.usc.edu.au/learn/courses-and-programs']
    start_urls = ['https://www.usc.edu.au/learn/courses-and-programs/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of the Sunshine Coast (USC)"
    uidPrefix = "AU-USC-"
    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "artist diploma": "5",
        "executive master": "11",
        # "foundation certificate": "4"
    }

    campus_map = {
        "Sunshine Coast": "821",
        "Moreton Bay": "822",
        "Caboolture": "823",
        "South Bank": "824",
        "SouthBank": "824",
        "Fraser Coast": "825",
        "Gympie": "826",
        "Sippy Downs": "828"
    }

    holder = []

    def parse(self, response):
        categories = response.css("div.grid-studyareas a::attr(href)").getall()
        for category in categories:
            yield response.follow(category, callback=self.category_parse)

    def category_parse(self, response):
        courses = response.css("#exploreYourStudyOptions a::attr(href)").getall()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1.mb-0::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees)

        campuses = response.xpath("//dd[preceding-sibling::dt[contains(text(),'Study location')]]//li/text()").getall()
        campuses = " ".join(campuses)
        holder = []
        for key in list(self.campus_map.keys()):
            if key in campuses:
                holder.append(self.campus_map[key])

        if holder:
            course_item["campusNID"] = "|".join(list(set(holder)))
            if "Online" in campuses:
                course_item["modeOfStudy"] = "In person|Online"
            else:
                course_item["modeOfStudy"] = "In person"

        elif "Online" in campuses:
            course_item["modeOfStudy"] = "Online"

        course_code = response.xpath("//dd[preceding-sibling::dt[contains(text(),'USC program code')]]/text()").get()
        if course_code:
            course_item["courseCode"] = course_code

        cricos = response.xpath("//dd[preceding-sibling::dt[contains(text(),'CRICOS code')]]/text()").get()
        if cricos:
            course_item["cricosCode"] = cricos

            int_fee = response.xpath("//dd[preceding-sibling::dt[contains(text(),'Estimated total tuition fee')]]/text()").get()
            annual_int_fee = response.xpath("//dd[preceding-sibling::dt[contains(text(),'Annual tuition fee')]]/text()").get()
            if int_fee:
                int_fee = int_fee.strip("A$").replace(",", "")
                course_item["internationalFeeTotal"] = int_fee
            if annual_int_fee:
                annual_int_fee = annual_int_fee.strip("A$").replace(",", "")
                course_item["internationalFeeAnnual"] = annual_int_fee

        duration = response.xpath("//dd[preceding-sibling::dt[contains(text(),'Duration')]]/text()").get()
        if duration:
            pattern = re.sub("[\d\.]+", "_", duration)
            if pattern not in self.holder:
                self.holder.append(pattern)

        print(self.holder)

        # if "flag" in course_item:
        #     yield course_item
