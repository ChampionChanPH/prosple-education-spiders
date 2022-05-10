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


class WaiSpiderSpider(scrapy.Spider):
    name = 'wai_spider'
    start_urls = ['https://www.angliss.edu.au/courses/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "William Angliss Institute"
    uidPrefix = "AU-WAI-"

    campuses = {
        "Sydney": "509",
        "Adelaide": "508",
        "National": "510",
        "Ballarat": "506",
        "North Sydney": "504",
        "Canberra": "505",
        "Strathfield": "503",
        "Melbourne": "501",
        "Brisbane": "502"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "undergraduate certificate": "4",
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
        categories = response.css("div.row a::attr(href)").getall()

        categories.remove("/courses/tourism/")
        categories.append("/courses/tourism/tourism/")
        categories = [x for x in categories if x != ""]

        for item in categories:
            yield response.follow(item, callback=self.category_parse)

    def category_parse(self, response):
        courses = response.css("div.row a::attr(href)").getall()

        for item in courses:
            yield SplashRequest(response.urljoin(item), callback=self.course_parse, args={'wait': 20}, meta={'url': response.urljoin(item)})

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.meta['url']
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.meta['url']

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_code = re.findall("\(([A-Z0-9]+?)\)", course_name)
            if course_code:
                course_item["courseCode"] = ", ".join(set(course_code))
            course_name = re.sub(" \([A-Z0-9]+?\)", "", course_name)
            course_name = re.sub("Dual Qualification - ", "", course_name)
            course_item.set_course_name(make_proper(
                course_name.strip()), self.uidPrefix)

        overview = response.xpath(
            "//*[text()='Course Description']/following-sibling::*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        start = response.xpath(
            "//div[@class='c-detail' and */text()='Course Intake']").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              "and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
