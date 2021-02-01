# -*- coding: utf-8 -*-
# by Christian Anasco

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


class WsuonlineSpiderSpider(scrapy.Spider):
    name = 'wsuonline_spider'
    start_urls = ['https://online.westernsydney.edu.au/online-courses/']
    institution = "Western Sydney University"
    uidPrefix = "AU-WSU-ON-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    campuses = {
        "Melbourne": "701",
        "Lismore": "695",
        "Gold Coast": "696",
        "Perth": "700",
        "Sydney": "699",
        "Tweed Heads": "698",
        "Coffs Harbour": "697",
        "National Marine Science Centre": "694",
    }

    numbers = {
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'nine': '9',
        'ten': '10',
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
        # courses = response.xpath("//a[@class='read-more']")
        # yield from response.follow_all(courses, callback=self.course_parse)

        course = 'https://online.westernsydney.edu.au/online-courses/nursing-midwifery/bachelor-of-nursing/'
        yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//p[@id='breadcrumbs']/following-sibling::*[1]/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//p[@id='breadcrumbs']/following-sibling::*[1]/following-sibling::*").getall()
        holder = []
        for item in overview:
            if not re.search('^<(p|o|u|d)', item):
                break
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder if strip_tags(x) != '']
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        intake = response.xpath(
            "//div[contains(@class, 'course-callout')]/*[text()='Start Date']/following-sibling::*").get()
        start_holder = []
        if intake:
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
        if start_holder:
            course_item['startMonths'] = '|'.join(start_holder)

        duration = response.xpath(
            "//div[contains(@class, 'course-callout')]/*[text()='Duration']/following-sibling::*").get()
        if duration:
            for num in self.numbers:
                duration = re.sub(num, self.numbers[num], duration, flags=re.I | re.M)
            print(duration)
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
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
                    # course_item["durationMinFull"] = float(duration_full[0][0])
                    # self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        entry = response.xpath("//div[@class='floating-caption']/*[text()='ENTRY CRITERIA' or text()='Entry "
                               "criteria']/following-sibling::*").getall()
        holder = []
        for item in entry:
            if not re.search('^<(p|o|u|d)', item):
                break
            else:
                holder.append(item)
        if holder:
            course_item['entryRequirements'] = strip_tags(''.join(holder), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        dom_fee = response.xpath(
            "//div[contains(@class, 'course-callout')]/*[text()='Fees (estimated)']/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        career = response.xpath("//div[@class='container'][*/*/*/text()='Career "
                                "Opportunities']/following-sibling::*//div[@class='content']/*").getall()
        if career:
            course_item['careerPathways'] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        course_item['modeOfStudy'] = 'Online'

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
