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


class LalSpiderSpider(scrapy.Spider):
    name = 'lal_spider'
    start_urls = ['https://www.languagelinks.wa.edu.au/our-courses/ielts-academic-english-eiap/',
                  'https://www.languagelinks.wa.edu.au/our-courses/cambridge-english-exam-courses/',
                  'https://www.languagelinks.wa.edu.au/our-courses/general-english/']
    institution = "Language Links"
    uidPrefix = "AU-LAL-"

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

    campuses = {
        "Northbridge": "30912"
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
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//*[contains(text(), 'CRICOS Course Code')]/text()").get()
        if course_name:
            name = re.sub('\s-.*', '', course_name)
            course_item.set_course_name(name.strip(), self.uidPrefix)

        cricos = re.findall("\d{6}[0-9a-zA-Z]", course_name, re.M)
        if cricos:
            course_item['cricosCode'] = ', '.join(cricos)
            course_item["internationalApps"] = 1

        overview = response.xpath("//div[@class='gdlr-core-pbf-element'][contains(*//text(), 'CRICOS Course "
                                  "Code')]/following-sibling::*/*/*/*").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            overview = [x for x in overview if re.search('^<[phou]', x)]
            course_item["overview"] = strip_tags(''.join(overview), False)

        course_item['campusNID'] = self.campuses['Northbridge']
        course_item['startMonths'] = '01|02|03|04|05|06|07|08|09|10|11|12'
        if course_item['courseName'] == 'Cambridge English Exam Preparation Courses':
            course_item['startMonths'] = '03|09'

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
