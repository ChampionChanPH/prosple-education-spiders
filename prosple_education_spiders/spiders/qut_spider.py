# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import strip_tags


class QutSpiderSpider(scrapy.Spider):
    name = 'qut_spider'
    allowed_domains = ['www.qut.edu.au', 'qut.edu.au']
    start_urls = ['https://www.qut.edu.au/study/undergraduate-study',
                  'https://www.qut.edu.au/study/postgraduate']
    institution = "QUT (Queensland University of Technology)"
    uidPrefix = "AU-QUT-"

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
        study_area = response.xpath("//ul[@class='study-area-links']/li/a/@href").getall()

        for item in study_area:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[@id='course-category-listing-panel-tabs']/a[not(contains(@data-target, "
                             "'Overview-tab'))]/@href").getall()

        for item in sub:
            yield response.follow(item, callback=self.list_parse)

    def list_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'study-level')]//a/@href").getall()

        courses = ["https://www.qut.edu.au/courses/bachelor-of-education-early-childhood?international"]
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

        course_name = response.xpath("//h1/span/text()").get().strip()
        course_item.set_course_name(course_name, self.uidPrefix)

        overview_summary = response.xpath("//div[contains(@class, 'hero__header__blurb')]/text()").get().strip()
        if overview_summary == "":
            overview_summary = response.xpath("//div[contains(@class, 'hero__header__blurb')]/p/text()").get().strip()
        if overview_summary is not None:
            course_item["overviewSummary"] = overview_summary

        overview = response.xpath("//*[contains(text(), 'Highlights')]/following-sibling::ul").get()
        if overview is not None:
            course_item["overview"] = overview

        rank = response.xpath("//dd[@class='rank']/text()").get().strip()
        if rank is not None:
            try:
                course_item["minScoreNextIntake"] = float(rank)
            except ValueError:
                course_item["minScoreNextIntake"] = rank

        location = response.xpath("//dt[contains(text(), 'Campus')]/following-sibling::dd").get()
        campus_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(set(campus_holder))

        cricos = response.xpath("//dt[contains(text(), 'CRICOS')]/following-sibling::dd/text()").get().strip()
        if cricos is not None:
            course_item["cricosCode"] = cricos

        duration = response.xpath("//div[@class='quick-box-inner']//dt[contains(text(), "
                                  "'Duration')]/following-sibling::dd[contains(@data-course-audience, "
                                  "'DOM')]").getall()
        if len(duration) > 0:
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.DOTALL | re.M)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
                                       duration, re.DOTALL | re.M)
            if len(duration_full) > 0:
                course_item["durationMinFull"] = float(duration_full[0][0])
                for item in self.teaching_periods:
                    if re.search(item, duration_full[0][1], re.I):
                        course_item["teachingPeriod"] = self.teaching_periods[item]
            if len(duration_part) > 0:
                course_item["durationMinPart"] = float(duration_part[0][0])

        yield course_item
