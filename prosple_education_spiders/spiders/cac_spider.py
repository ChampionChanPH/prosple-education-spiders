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


class CacSpiderSpider(scrapy.Spider):
    name = 'cac_spider'
    allowed_domains = ['www.canningcollege.wa.edu.au', 'canningcollege.wa.edu.au']
    start_urls = ['http://www.canningcollege.wa.edu.au/Courses.htm']
    banned_urls = ['/Courses-Links_to_WA_Universities.htm']
    institution = "Canning College"
    uidPrefix = "AU-CAC-"

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
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "year 10": "9",
        "year 11": "9",
        "year 12 - western australian certificate": "9",
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
        categories = response.xpath("//div[@class='head']/a/@href").getall()

        for item in categories:
            if item not in self.banned_urls:
                if item in ['/Courses-Bridging_Programs.htm',
                            '/Courses-Year_11_Secondary_Studies.htm',
                            '/Courses-Year_10_Secondary_Studies.htm']:
                    yield response.follow(item, callback=self.course_parse)
                else:
                    yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//ul[contains(@class, 'list-un')]//a/@href").getall()
        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//a[@class='active']/text()").get()
        course_name = re.sub("[0-9]+[a-zA-Z]+", "", course_name)
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[contains(@class, 'bodyContent_Body')]/*").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            for item in overview:
                holder = []
                if not re.search("^<p><img", item):
                    holder.append(item)
                if holder:
                    course_item["overview"] = strip_tags("".join(holder), False)

        duration = response.xpath("//div[contains(@class, 'bodyContent_Course_Duration')]").getall()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\s)",
                                       duration, re.I | re.M | re.DOTALL)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)

        entry = response.xpath("//div[contains(@class, 'bodyContent_Prerequisites')]/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags("".join(entry), False)

        apply = response.xpath("//div[contains(@class, 'bodyContent_Enrolment_Details')]/*").getall()
        if apply:
            course_item["howToApply"] = strip_tags("".join(apply), False)

        # start = response.xpath("//div[contains(@class, 'bodyContent_Course_Dates')]").getall()
        # if start:
        #     start = "".join(start)
        #     start_holder = []
        #     for month in self.months:
        #         if re.search("Classes:" + ".*?" + month, start, re.I | re.M | re.DOTALL):
        #             start_holder.append(self.months[month])
        #     if start_holder:
        #         course_item["startMonths"] = "|".join(start_holder)

        cricos = response.xpath("//div[contains(@class, 'bodyContent_Course_Code')]").getall()
        if cricos:
            cricos = "".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item
