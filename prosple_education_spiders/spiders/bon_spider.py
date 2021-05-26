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
                course_item[field_to_update] = float(course_item[field_to_use]) *\
                                               float(course_item["durationMinFull"]) / 12
        if course_item["teachingPeriod"] == 52:
            if float(course_item["durationMinFull"]) < 52:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) *\
                                               float(course_item["durationMinFull"]) / 52


class BonSpiderSpider(scrapy.Spider):
    name = 'bon_spider'
    allowed_domains = ['bond.edu.au']
    start_urls = ['https://bond.edu.au/future-students/study-bond/search-program']
    banned_urls = ['//bond.edu.au/program/study-tours']
    institution = "Bond University"
    uidPrefix = "AU-BON-"

    degrees = {
        "graduate certificate": "7",
        'bond-bbt graduate certificate': '7',
        "executive graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "the diploma": "5",
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
        courses = response.xpath("//div[@class='tab-content']//a/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='page-title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[contains(text(), 'About the program')]/following-sibling::*[1]/div["
                                  "@id='show-more-0']/*/text()").getall()
        if not overview:
            overview = response.xpath(
                "//*[contains(text(), 'About the program')]/following-sibling::*[1]//text()").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags("".join(overview), remove_all_tags=False, remove_hyperlinks=True)

        start = response.xpath("//td[contains(*/text(), 'Starting semesters')]/following-sibling::*").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month + " " + str(date.today().year), start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        study = response.xpath("//td[contains(*/text(), 'Mode')]/following-sibling::*").get()
        if study:
            study_holder = []
            if re.search("on campus", study, re.I | re.M):
                study_holder.append("In Person")
            if re.search("online", study, re.I | re.M):
                study_holder.append("Online")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        career = response.xpath("//div[contains(*/*/text(), 'Professional outcomes')]/following-sibling::*[1]//p").getall()
        if career:
            course_item["careerPathways"] = strip_tags("".join(career), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath("//h4[contains(text(), 'Credit for prior study')]/following-sibling::*").get()
        if credit:
            course_item["creditTransfer"] = strip_tags(credit, remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath("//h4[contains(text(), 'How to apply')]/following-sibling::*").getall()
        if apply:
            course_item["howToApply"] = strip_tags("".join(apply), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//td[contains(*/text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration = ''.join(duration)
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\(?s?\)?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\(?s?\)?\s+?part)",
                duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        course_code = response.xpath("//td[contains(*/text(), 'Program code')]/following-sibling::*/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        course_structure = response.xpath("//div[contains(*/*/text(), 'Structure and "
                                          "subjects')]/following-sibling::*[1]/*/*").getall()
        if course_structure:
            course_item["courseStructure"] = strip_tags("".join(course_structure),
                                                        remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath("//td[contains(*/text(), 'CRICOS code')]/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_item["campusNID"] = "511"

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item
