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


class RmiSpiderSpider(scrapy.Spider):
    name = 'rmi_spider'
    start_urls = ['https://www.rmit.edu.au/study-with-us']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "RMIT University"
    uidPrefix = "AU-RMI-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "phd": "6",
        "certificate": "4",
        "victorian certificate": "4",
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
        "Hobart": "710",
        "Croydon": "708",
        "Off-Campus": "709",
        "Wantirna": "707",
        "Richmond Football Club": "706",
        "Melbourne": "704",
        "Hawthorn": "703"
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

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.category_parse, args={'wait': 20})

    def category_parse(self, response):
        categories = response.xpath("//div[@class='target_EF']//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[contains(@class, 'columnlinklist__content--box')]//a["
                             "@data-analytics-type='columnlinklist']/@href").getall()

        for item in sub:
            yield SplashRequest(response.urljoin(item), callback=self.link_parse, args={'wait': 20})

    def link_parse(self, response):
        courses = response.xpath("//a[@data-analytics-type='program list']/@href").getall()

        for item in courses:
            yield response.follow(response.urljoin(item), callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                  "'Overview')]/following-sibling::div[1]/div[contains(@class, "
                                  "'extended-desc')]/*").getall()
        if not overview or strip_tags(overview).strip() == '':
            overview = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                      "'Details')]/following-sibling::div[1]/div[contains(@class, "
                                      "'extended-desc')]/p").getall()
        if overview:
            course_item['overview'] = strip_tags(''.join(overview), False)

        career = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                "'Career')]/following-sibling::div[1]/div[contains(@class, "
                                "'extended-desc')]/*").getall()
        if career:
            course_item['careerPathways'] = strip_tags(''.join(career), False)

        yield course_item

