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


class MwtSpiderSpider(scrapy.Spider):
    name = 'mwt_spider'
    allowed_domains = ['www.mwtrain.com.au', 'mwtrain.com.au']
    start_urls = [
        'http://www.mwtrain.com.au/our-courses/tae80113-graduate-diploma-of-adult-language-literacy-and-numeracy-practice/',
        'http://www.mwtrain.com.au/our-courses/tae80213-graduate-diploma-of-adult-language-literacy-and-numeracy-leadership/']
    institution = "MW Training Consultants"
    uidPrefix = "AU-MWT-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
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
        yield SplashRequest(response.request.url, callback=self.course_parse, args={'wait': 20})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        title = response.xpath("//title/text()").get()
        split_title = re.findall("(\w+):\s(.+)\s–", title, re.DOTALL)
        if split_title:
            course_code, course_name = split_title[0]
            course_item["courseCode"] = course_code.strip()
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[preceding-sibling::*[contains(text(), 'Course Description')] and "
                                  "following-sibling::*[contains(text(), 'Possible job titles')]]").getall()
        if overview:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, False)

        career = response.xpath(
            "//*[preceding-sibling::*[contains(text(), 'Possible job titles')]]").get()
        if career:
            course_item["careerPathways"] = strip_tags(career, False)

        duration = response.xpath(
            "//div[contains(a/text(), 'Volume of Learning')]/following-sibling::*//text()").get()
        duration = re.findall("(\d*\.?\d+)\s–\s(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                              duration, re.M)
        if len(duration) > 0:
            course_item["durationMinFull"] = float(duration[0][0])
            course_item["durationMinPart"] = float(duration[0][1])
            self.get_period(duration[0][2], course_item)

        fee = response.xpath(
            "//div[contains(a/text(), 'Course Cost')]/following-sibling::*//text()").get()
        if fee:
            fee = re.findall("\$\d*,?\d+", fee, re.M)
            if len(fee) > 0:
                fee = float(re.sub("[$,]", "", fee[0]))
                course_item["domesticFeeAnnual"] = fee

        entry = response.xpath(
            "//div[contains(a/text(), 'Entry Requirements')]/following-sibling::*/*").getall()
        if len(entry) == 0:
            entry = ""
        else:
            entry = "".join(entry)
        assessment = response.xpath(
            "//div[contains(a/text(), 'Assessment')]/following-sibling::*/*").getall()
        if len(assessment) == 0:
            assessment = ""
        else:
            assessment = "<br><p><strong>Assessment</strong></p>" + \
                "".join(assessment)
        course_item["entryRequirements"] = strip_tags(
            entry + assessment, False)

        unit_competency = response.xpath("//div[contains(a/text(), 'Units of competency "
                                         "required')]/following-sibling::*/*").getall()
        if len(unit_competency) == 0:
            unit_competency = ""
        else:
            unit_competency = "".join(unit_competency)
        unit_required = response.xpath(
            "//div[contains(a/text(), 'Units Required')]/following-sibling::*/*").getall()
        if len(unit_required) == 0:
            unit_required = ""
        else:
            unit_required = "".join(unit_required)
        course_item["courseStructure"] = strip_tags(
            unit_competency + unit_required, False)

        apply = response.xpath(
            "//div[contains(a/text(), 'How to Enrol')]/following-sibling::*/*").getall()
        if len(apply) > 0:
            apply = "".join(apply)
            course_item["howToApply"] = strip_tags(apply, False)

        course_item["modeOfStudy"] = "Online"
        course_item["startMonths"] = "01|02|03|04|05|06|07|08|09|10|11|12"

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item
