# -*- coding: utf-8 -*-
# by Christian Anasco
# 8/21/2020 having difficulties getting the data from the course page

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


class GriSpiderSpider(scrapy.Spider):
    name = 'gri_spider'
    # start_urls = ['https://www.griffith.edu.au/study/degrees?term=&studentType=domestic&studentType=international'
    #               '&academicTermYear=2020']
    start_urls = ['https://www.griffith.edu.au/study/degrees?term=&studentType=domestic&studentType=international']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Griffith University"
    uidPrefix = "AU-GRI-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
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

    lua_script = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(2.0))
          return {
            html = splash:html(),
          }
        end
    """

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.sub_parse, args={'wait': 20})

    def sub_parse(self, response):
        courses = response.xpath("//div[@class='tr']//a/@href").getall()

        courses = ['https://www.griffith.edu.au/study/degrees/bachelor-of-arts-1016']
        for item in courses:
            # yield SplashRequest(response.urljoin(item), callback=self.course_parse,
            #                     args={'wait': 20}, meta={'url': response.urljoin(item)})
            yield SplashRequest(response.urljoin(item), callback=self.course_parse, endpoint='execute',
                                args={'lua_source': self.lua_script, 'url': response.urljoin(item), 'wait': 20},
                                meta={'url': response.urljoin(item)})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//title/text()").get()
        if course_name:
            course_name = re.sub('-.*', '', course_name, re.DOTALL)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        cricos = response.xpath("//dt[contains(@class, 'cricos-code')]/following-sibling::dd").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ', '.join(cricos)
                course_item["internationalApps"] = 1

        yield course_item