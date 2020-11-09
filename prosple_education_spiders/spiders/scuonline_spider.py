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


class ScuonlineSpiderSpider(scrapy.Spider):
    name = 'scuonline_spider'
    start_urls = ['https://online.scu.edu.au/courses/']
    institution = "Southern Cross University (SCU)"
    uidPrefix = "AU-SCU-ON-"

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
        "diploma": "5",
        "associate degree": "1",
        "vcal in victorian certificate": "9",
        "vcal in": "9",
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

    key_dates = {
        "1": "03",
        "2": "07",
        "3": "11"
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
        courses = response.xpath("//a[text()='Course details']/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(make_proper(course_name.strip()), self.uidPrefix)

        learn = response.xpath("//div[@class='learning-outcomes right']/*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), remove_all_tags=False)

        duration = response.xpath("//div[@class='vp-header'][*/text()='Duration']/following-sibling::*").get()
        if duration:
            course_item['durationRaw'] = strip_tags(duration, remove_all_tags=False)

        intake = response.xpath("//div[@class='vp-header'][*/text()='Intakes']/following-sibling::*").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        unit = response.xpath("//div[@class='vp-header'][*/text()='Units']/following-sibling::*").get()
        if unit:
            course_item['feesRaw'] = strip_tags(unit, remove_all_tags=False)

        fee = response.xpath("//div[@class='vp-header'][*/text()='Fees']/following-sibling::*").get()
        if fee:
            course_item['domesticFeeAnnual'] = strip_tags(fee, remove_all_tags=False)

        study = response.xpath("//div[@class='vp-header'][*/text()='Study mode']/following-sibling::*").get()
        if study:
            course_item['modeOfStudy'] = strip_tags(study, remove_all_tags=False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
