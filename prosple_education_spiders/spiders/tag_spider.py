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


class TagSpiderSpider(scrapy.Spider):
    name = 'tag_spider'
    start_urls = ['https://www.tafegippsland.edu.au/course_search?profile=_default&collection=fed-training-meta&query=']
    institution = "TAFE Gippsland"
    uidPrefix = "AU-TAG-"

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
        "vcal - victorian certificate": "9",
        "vce - victorian certificate": "9",
        "vce- victorian certificate": "9",
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
        "Dandenong": "58339",
        "Frankston": "58340",
        "Berwick": "58341",
        "Cranbourne": "58342",
        "Chisholm at 311": "58343",
        "Bass Coast": "58344",
        "Mornington Peninsula": "58345",
        "Workplace": "58346",
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
        courses = response.xpath("//ul[@id='search-results']//div[contains(@id, 'result')]/a")
        yield from response.follow_all(courses, callback=self.course_parse)

        next_page = response.xpath("//a[@rel='next']/@href").getall()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='course-description']/*").getall()
        holder = []
        for item in overview:
            if not re.search('^<(p|u|o)', item):
                break
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath("//div[contains(text(), 'Location')]/following-sibling::*").get()
        if location:
            course_item['campusNID'] = location

        intake = response.xpath("//div[contains(text(), 'Starting Date')]/following-sibling::*").get()
        if intake:
            holder = []
            for item in self.months.values():
                if re.search('/' + item + '/', intake, re.M):
                    holder.append(item)
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        study = response.xpath("//div[contains(text(), 'Study Mode')]/following-sibling::*").get()
        if study:
            course_item['modeOfStudy'] = study

        duration = response.xpath("//div[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            course_item['durationRaw'] = duration

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
