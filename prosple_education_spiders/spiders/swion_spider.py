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


class SwionSpiderSpider(scrapy.Spider):
    name = 'swion_spider'
    allowed_domains = ['www.swinburneonline.edu.au', 'swinburneonline.edu.au']
    start_urls = ['https://www.swinburneonline.edu.au/online-courses']
    banned_urls = []
    institution = "Swinburne University of Technology"
    uidPrefix = "AU-SWI-ON-"

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
        categories = response.xpath("//div[@id='disciplines']//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = ['https://www.swinburneonline.edu.au/online-courses/health/diploma-of-nursing',
                   'https://www.swinburneonline.edu.au/online-courses/technology/bachelor-of-information-and'
                   '-communication-technology']

        ug = response.xpath("//div[@id='undergraduate']//a/@href").getall()
        if ug:
            courses.extend(ug)

        vet = response.xpath("//div[@id='vet']//a/@href").getall()
        if vet:
            courses.extend(vet)

        pg = response.xpath("//div[@id='postgraduate']//a/@href").getall()
        if pg:
            courses.extend(pg)

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1//text()").getall()
        if course_name:
            course_name = [x.strip() for x in course_name]
            course_name = " ".join(course_name)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_item["modeOfStudy"] = "Online"
        course_item["campusNID"] = "709"

        overview = response.xpath("//div[contains(@id, 'overview')]//div[@class='the_copy']/*").getall()
        if overview:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, False)

        summary = response.xpath("//div[contains(@id, 'overview')]//div[@class='the_copy']/*[1]/text()").getall()
        if summary:
            summary = "".join(summary)
            course_item.set_summary(summary)

        entry = response.xpath("//div[@id='entry']//div[@id='entry_the_copy']/*").getall()
        if entry:
            entry = "".join(entry)
            course_item["entryRequirements"] = strip_tags(entry, False)

        start = response.xpath("//li[@class='date']/*[contains(text(), 'Start')]/following-sibling::*").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)
            if re.search("fortnight", start, re.I | re.M):
                course_item["startMonths"] = "01|02|03|04|05|06|07|08|09|10|11|12"

        duration = response.xpath("//li[@class='duration']/*[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M | re.DOTALL)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item