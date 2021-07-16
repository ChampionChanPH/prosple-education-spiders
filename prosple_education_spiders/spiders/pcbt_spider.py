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


class PcbtSpiderSpider(scrapy.Spider):
    name = 'pcbt_spider'
    start_urls = ['https://pcbt.wa.edu.au/']
    banned_urls = []
    institution = 'Perth College of Business & Technology (PCBT)'
    uidPrefix = 'AU-PCBT-'

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        'fast track dual qualification advanced diploma': '5',
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
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
        "Dec": "12",
        "/1/": "01",
        "/2/": "02",
        "/3/": "03",
        "/4/": "04",
        "/5/": "05",
        "/6/": "06",
        "/7/": "07",
        "/8/": "08",
        "/9/": "09",
        "/10/": "10",
        "/11/": "11",
        "/12/": "12",
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//a[span/text()='Courses']/following-sibling::*//a")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        name = response.xpath("//h1[@class='title']/text()").get()
        if re.findall('(.*) – [A-Z]+[0-9]+', name, re.DOTALL):
            course_name, course_code = re.findall('(.*) – ([A-Z]+[0-9]+)', name, re.DOTALL)[0]
        else:
            course_name = name
            course_code = None
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)
        if course_code:
            course_item['courseCode'] = course_code.strip()

        overview = response.xpath(
            "//div[a/text()='Enrol to this course now']/preceding-sibling::*//div[@class='wpb_wrapper']/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath(
            "//h4[text()='Nationally Recognised Qualification']/following-sibling::*//text()").getall()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", ' '.join(cricos), re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)

        intake = response.xpath("//h4[text()='Intakes']/following-sibling::*").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.I | re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)
            if re.search('every month', intake, re.I | re.M):
                course_item["startMonths"] = '01|02|03|04|05|06|07|08|09|10|11|12'

        dom_fee = response.xpath("//h4[text()='Course Fees']/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        duration = response.xpath("//h4[text()='Course Duration']/following-sibling::*").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?full.time)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?part.time)",
                duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration,
                                           re.I | re.M | re.DOTALL)
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

        career = response.xpath("//h4[text()='Career Opportunities']/following-sibling::*").get()
        if career:
            course_item['careerPathways'] = strip_tags(career, remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        course_item['group'] = 23
        course_item['canonicalGroup'] = 'StudyPerth'

        yield course_item
