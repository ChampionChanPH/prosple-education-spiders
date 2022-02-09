# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


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


class RmionlineSpiderSpider(scrapy.Spider):
    name = 'rmionline_spider'
    start_urls = ['https://studyonline.rmit.edu.au/online-programs']
    institution = "RMIT University"
    uidPrefix = "AU-RMI-ON-"

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
        "vcal - victorian certificate": "9",
        "non-award": "13",
        "no match": "15"
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

    campuses = {
        "Online": "57035"
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
        courses = response.xpath("//a[text()='View program']/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath("//h1/following-sibling::*").get()
        if summary:
            course_item.set_summary(strip_tags(summary))

        overview_holder = []
        header = response.xpath("//section[contains(@class, 'program-overview')]/header/text()").get()
        if header:
            overview_holder.append(f"<strong>{header.strip()}</strong>")
        overview = response.xpath("//section[contains(@class, 'program-overview')]/header/following-sibling::div["
                                  "@class='content']/*[self::p or self::ul or self::ol]").getall()
        if overview:
            overview_holder.extend(overview)
        if overview_holder:
            course_item["overview"] = strip_tags(''.join(overview_holder),
                                                 remove_all_tags=False, remove_hyperlinks=True)

        course_count = response.xpath("//div[@class='quick-facts']/div[contains(@class, 'qf-left')]/text()").get()
        if course_count:
            try:
                course_count = int(course_count)
            except ValueError:
                course_count = None

        dom_fee = response.xpath("//div[@id='qf-desc3']").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee and course_count:
                course_item["domesticFeeTotal"] = max(dom_fee) * course_count
                course_item["internationalFeeTotal"] = max(dom_fee) * course_count

        duration = response.xpath("//div[@id='qf-desc1']").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?.*?full.time)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?.*?part.time)",
                duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
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

        intake = response.xpath("//div[@id='qf-desc2']").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        learn = response.xpath("//section[contains(@class, 'why-rmit-header')]/following-sibling::*/*/*").getall()
        if learn:
            learn = [x for x in learn if not re.search('<img', x)]
            course_item["whatLearn"] = strip_tags(''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        study = response.xpath("//section[contains(@class, 'program-study')]/header/following-sibling::div["
                               "@class='content']/*[self::p or self::ul or self::ol][1]").get()
        if study and 'whatLearn' in course_item:
            course_item["whatLearn"] = course_item["whatLearn"] + '<strong>What you will study</strong>' + study

        entry = response.xpath("//section[contains(@class, 'entry-req')]/header/following-sibling::div["
                               "@class='content']/*[self::p or self::ul or self::ol][1]").get()
        if entry:
            course_item["entryRequirements"] = strip_tags(entry, remove_all_tags=False, remove_hyperlinks=True)

        # course_item['campusNID'] = self.campuses['Online']
        course_item['modeOfStudy'] = 'Online'
        course_item['internationalApps'] = 1

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        yield course_item
