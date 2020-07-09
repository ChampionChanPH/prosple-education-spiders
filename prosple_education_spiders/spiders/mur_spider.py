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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


class MurSpiderSpider(scrapy.Spider):
    name = 'mur_spider'
    allowed_domains = ['search.murdoch.edu.au', 'murdoch.edu.au']
    start_urls = ['https://search.murdoch.edu.au/s/search.html?collection=mu-course-search']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    courses = []
    institution = "Murdoch University"
    uidPrefix = "AU-MUR-"

    campuses = {
        "On-line Learning": "11707",
        "Gippsland - Churchill": "11716",
        "Broadmeadows": "607",
        "Flexible Delivery - Wimmera": "606",
        "Chadstone / Ballarat": "605",
        "Flexible Delivery - Berwick": "604",
        "Flexible Delivery - Ballarat": "603",
        "Horsham and Stawell": "602",
        "Ballarat - Camp St": "601",
        "Gillies Street": "600",
        "External": "599",
        "Flexible Delivery - Gippsland": "598",
        "Workplace - Other Victoria": "597",
        "Workplace - Ballarat": "596",
        "Ballarat": "590",
        "Mt Rowan - Rural Skills Centre": "595",
        "Wimmera - Horsham": "594",
        "Berwick": "593",
        "Ballarat - Mt Helen": "592",
        "Ballarat - SMB": "591",
        "Brisbane": "51245"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "research masters with training": research_coursework,
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.sub_parse, args={'wait': 20})

    def sub_parse(self, response):
        courses = response.xpath("//li[@class='search-tier']/following-sibling::*//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//a[@rel='next']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.sub_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h3[contains(@class, 'h--regular')]/text()").get()
        if course_name.strip() == '' or re.search("fieldname", course_name):
            course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[text()='Course Description']/following-sibling::*").getall()
        holder = []
        for item in overview:
            if (not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M)) or \
                    re.search("class=", item, re.M):
                break
            else:
                holder.append(item)
        if len(holder) == 1:
            course_item.set_summary(strip_tags(holder[0]))
            course_item["overview"] = strip_tags("".join(holder), False)
        if len(holder) > 1:
            course_item.set_summary(strip_tags(holder[0] + holder[1]))
            course_item["overview"] = strip_tags("".join(holder), False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/", "\+"], type_delims=["of", "in", "by", "with"])

        yield course_item