# -*- coding: utf-8 -*-
# by Christian Anasco
# "startMonths" is for year 2020 and 2021

from ..standard_libs import *


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


class AiwtSpiderSpider(scrapy.Spider):
    name = 'aiwt_spider'
    allowed_domains = ['www.aiwt.edu.au', 'aiwt.edu.au']
    start_urls = ['https://www.aiwt.edu.au/new-students-domestic/courses/',
                  'https://www.aiwt.edu.au/new-students-international/courses/']
    institution = "Australia-International Institute of Workplace Training (AIWT)"
    uidPrefix = "AU-AIWT-"

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
        "non-award": "13",
        "no match": "15"
    }

    def parse(self, response):
        courses = response.xpath("//div[@class='other-courses']/a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        complete_name = max(response.xpath("//h1/text()").getall())
        if complete_name is not None:
            course = complete_name.strip()
            course_code = re.findall("^[a-zA-Z]+[0-9]+", course)
            if len(course_code) > 0:
                course_item["courseCode"] = course_code[0]
            if "courseCode" in course_item:
                course = re.sub(course_item["courseCode"], "", course)
            course_item.set_course_name(course.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='course-overview']/text()").get()
        if overview is not None:
            course_item["overview"] = overview
        if "overview" not in course_item:
            overview = "Learn more about studying " + course_item["courseName"] + " at " + self.institution + "."
            course_item["overview"] = overview

        career = max(response.xpath("//div[contains(h2, 'Career Prospects')]/text()").getall())
        if career is not None:
            course_item["careerPathways"] = career.strip()

        cricos = response.xpath("//div[contains(text(), 'CRICOS CODE')]/text()").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if len(cricos) > 0:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1

        course_item["startMonths"] = "02|04|07|10"
        course_item["campusNID"] = "30895|30896"

        course_item.set_sf_dt(self.degrees)

        yield course_item
