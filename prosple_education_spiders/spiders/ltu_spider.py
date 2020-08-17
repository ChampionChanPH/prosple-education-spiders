# -*- coding: utf-8 -*-
# by Christian Anasco
# having difficulties getting the details on the course pages

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


class LtuSpiderSpider(scrapy.Spider):
    name = 'ltu_spider'
    start_urls = ['https://www.latrobe.edu.au/courses/a-z']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    institution = 'La Trobe University'
    uidPrefix = 'AU-LTU-'

    campuses = {
        "North Campus": "53669",
        "City Campus": "53670",
        "South Campus": "53671",
        "Distance": "53672"
    }

    degrees = {
        "graduate certificate": "7",
        "postgraduate certificate": "7",
        "graduate diploma": "8",
        "postgraduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "senior executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "doctoral program": "6",
        "certificate": "4",
        "specialist certificate": "4",
        "professional certificate": "14",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "juris doctor": "10",
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
        categories = response.xpath("//ul[@class='double-list']/li/a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        boxes = response.xpath("//div[@id='ajax-course-list']/article[@data-filters]")

        for item in boxes:
            url = item.xpath(".//h3/a/@href").get()
            location = item.xpath(".//p[contains(@class, 'course-list-atar')]").get()
            start = item.xpath(".//p[contains(@class, 'course-start-dates')]").get()
            if url:
                yield SplashRequest(url, callback=self.course_parse, endpoint='execute',
                                    args={'lua_source': self.lua_script, 'url': url, 'wait': 20},
                                    meta={'location': location, 'url': url, 'start': start})

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.meta['url']
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_item['campusNID'] = response.meta['location']

        overview = response.xpath("//p[@class='footnote']").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            course_item['overview'] = strip_tags(''.join(overview), False)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
