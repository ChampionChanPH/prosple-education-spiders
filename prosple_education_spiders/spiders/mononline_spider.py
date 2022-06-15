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


class MononlineSpiderSpider(scrapy.Spider):
    name = 'mononline_spider'
    start_urls = ['https://online.monash.edu/online-courses/']
    institution = 'Monash University'
    uidPrefix = "AU-MON-ON-"
    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "undergraduate certificate": "4",
        "certificate iv": "4",
        "certificate iii": "4",
        "certificate ii": "4",
        "certificate i": "4",
        "certificate": "4",
        "diploma": "5",
        "undergraduate diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Sydney": "778",
        "Fremantle": "777",
        "Broome": "779"
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
        "Dec": "12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath(
            "////div[contains(@class, 'course-archive__courses')]/a/@href").getall()
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.css("section.course-overview div.left *").getall()
        if overview:
            overview = [x for x in overview if strip_tags(x) != ""]
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.css("section.course-overview div.right ul").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(
                ''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//div[@id='entry']//div[@class='card-body']/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        unit = response.xpath(
            "//p[text()='Units']/following-sibling::*/text()").get()
        if unit:
            try:
                unit = float(unit)
            except:
                unit = None
        unit_fee = response.xpath(
            "//div[@id='fees']//div[@class='card-body']/*").getall()
        if unit_fee:
            unit_fee = ''.join(unit_fee)
            unit_fee = re.findall(
                "\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?\sper\sunit", unit_fee, re.M)
            unit_fee = [float(''.join(x)) for x in unit_fee]
            unit_fee = max(unit_fee)
        if unit and unit_fee:
            course_item["domesticFeeTotal"] = unit * unit_fee

        intake = response.xpath(
            "//p[text()='Intakes']/following-sibling::*").get()
        start_holder = []
        if intake:
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
        if start_holder:
            course_item['startMonths'] = '|'.join(start_holder)

        course_item["modeOfStudy"] = "Online"

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
