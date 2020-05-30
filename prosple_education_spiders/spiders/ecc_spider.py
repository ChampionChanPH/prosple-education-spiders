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


class EccSpiderSpider(scrapy.Spider):
    name = 'ecc_spider'
    allowed_domains = ['www.edithcowancollege.edu.au', 'edithcowancollege.edu.au']
    start_urls = ['https://www.edithcowancollege.edu.au/']
    banned_urls = []
    institution = "Edith Cowan College"
    uidPrefix = "AU-ECC-"

    campuses = {
        "ECU Mt Lawley": "30907",
        "ECU Joondalup": "30908"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//a[@id='button-id-1911']/following-sibling::ul//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='headline-title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[contains(@class, 'course-description')]/*/text()").getall()
        if overview:
            overview = [x.strip() for x in overview]
            course_item["overview"] = strip_tags("".join(overview), remove_all_tags=False)
            course_item.set_summary("".join(overview))

        table = response.xpath("//table[@id='coursePrices']").get()
        if table:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", table, re.M)
            if cricos:
                cricos = set(cricos)
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_item["campusNID"] = "30907|30908"

        start = response.xpath("//div[@class='grayback']/*[contains(text(), 'Intakes')]/following-sibling::*").get()
        if start:
            start_holder = []
            for item in self.months:
                if re.search(item, start, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        duration = response.xpath("//div[@class='grayback']/*[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d*)\s?o?r?\s?(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M)
            if duration_full:
                if duration_full[0][0] == "":
                    course_item["durationMinFull"] = float(duration_full[0][1])
                else:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    course_item["durationMaxFull"] = float(duration_full[0][1])
                self.get_period(duration_full[0][2].lower(), course_item)

        course_item.set_sf_dt(self.degrees)

        if re.search("post.?graduate", course_item["courseName"], re.I | re.DOTALL):
            course_item["courseLevel"] = "Postgraduate"
            course_item["group"] = 4

        yield course_item


