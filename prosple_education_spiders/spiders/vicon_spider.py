# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


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
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class ViconSpiderSpider(scrapy.Spider):
    name = 'vicon_spider'
    allowed_domains = ['online.vu.edu.au']
    start_urls = ['https://online.vu.edu.au/online-courses']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Victoria University (VU)"
    uidPrefix = "AU-VIC-ON-"

    degrees = {
        "master": "11"
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.css("h3 a::attr(href)").getall()
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

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item["modeOfStudy"] = "Online"
        # course_item["campusNID"] = "57342"

        overview = response.css(".overviewbody p::text").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        intakes = response.css("span.study p::text").get()
        if intakes:
            intakes = convert_months(intakes.replace(" ", "").split(","))
            course_item["startMonths"] = "|".join(intakes)

        fees = response.css("span.fees p::text").get()
        units = response.css("span.units p::text").get()
        if fees and units:
            fee = re.findall("\$([\d\.\,]+)", fees)[0]
            unit = re.findall("^(\d+)", units)[0]
            course_item["domesticFeeTotal"] = float(
                fee.replace(",", ""))*float(unit)
            course_item["internationalFeeTotal"] = float(
                fee.replace(",", ""))*float(unit)

        duration = response.css("span.duration p::text").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?,?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?,?\s+?part)",
                duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                        / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        entry = response.xpath(
            "//ul[preceding-sibling::h3/text()='Entry requirements']").get()
        if entry:
            course_item["entryRequirements"] = cleanspace(entry)

        else:
            entry = response.xpath(
                "//p[preceding-sibling::h3/text()='Entry requirements']/text()").getall()
            if entry:
                course_item["entryRequirements"] = "\n".join(entry)

        titles = response.xpath(
            "//ul[preceding-sibling::h4/text()='Typical job titles']").get()
        if titles:
            course_item["careerPathways"] = cleanspace(titles)

        course_item.set_sf_dt(self.degrees, degree_delims=[
            "and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
