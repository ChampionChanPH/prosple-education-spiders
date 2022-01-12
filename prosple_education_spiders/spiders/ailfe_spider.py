# -*- coding: utf-8 -*-
# by Christian Anasco
import re

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


class AilfeSpiderSpider(scrapy.Spider):
    name = 'ailfe_spider'
    start_urls = ['https://www.ailfe.wa.edu.au/courses']
    banned_urls = ["https://www.ailfe.wa.edu.au/general-english"]
    institution = "Australian Institute of Language and Further Education (AILFE)"
    uidPrefix = "AU-AILFE-"

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
        "Perth Campus": "83028",
        "Sydney Campus": "83029",
        "Brisbane Campus": "83027"
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
        courses = response.xpath("//div[@data-testid='mesh-container-content']/div//li//a/@href").getall()

        for item in courses:
            if re.search("ailfe.wa.edu.au", item) and item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//div[contains(@id, 'comp-')][2]//h2[@class='font_2']//a//text()").getall()
        if not course_name:
            course_name = response.xpath("//div[contains(@id, 'comp-')][2]//h2[@class='font_2']//span//text()").getall()
        if course_name:
            course_name = "".join(course_name)
            course_name = course_name.replace("&nbsp;", " ")
            course_name = course_name.replace("\xa0", " ")
            if re.search("[A-Z0-9]+[A-Z0-9]+ ", course_name):
                course_code, course_name = re.split("\\s", strip_tags(course_name), maxsplit=1)
                course_item.set_course_name(strip_tags(course_name), self.uidPrefix)
                course_item["courseCode"] = strip_tags(course_code)
            else:
                course_item.set_course_name(strip_tags(course_name), self.uidPrefix)

        overview = response.xpath("//div[contains(@id, 'comp-') and not(contains(@id, 'comp-ik'))][last()]/*").getall()
        holder = []
        for item in overview:
            if not strip_tags(item):
                break
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath(
            "//div[contains(@id, 'comp-') and not(contains(@id, 'comp-ik'))][last()]/*[contains(*//text(), 'CRICOS')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(set(cricos))
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        duration = response.xpath("//div[contains(@id, 'comp-') and not(contains(@id, 'comp-ik'))][last()]/*[contains(*//text(), 'Course Duration')]/following-sibling::*").getall()
        holder = []
        for item in duration:
            if not strip_tags(item):
                break
            else:
                holder.append(item)
        if holder:
            duration = "".join(holder)
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
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
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)
            study_holder = []
            if re.search("face", duration, re.I | re.M):
                study_holder.append("In Person")
            if re.search("online", duration, re.I | re.M):
                study_holder.append("Online")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        entry = response.xpath(
            "//div[contains(@id, 'comp-') and not(contains(@id, 'comp-ik'))][last()]/*[contains(*//text(), 'Entry Requirements')]/following-sibling::*").getall()
        holder = []
        for item in entry:
            if not strip_tags(item):
                break
            else:
                holder.append(item)
        if holder:
            course_item["entryRequirements"] = strip_tags(''.join(holder), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        career = response.xpath(
            "//div[contains(@id, 'comp-') and not(contains(@id, 'comp-ik'))][last()]/*[contains(*//text(), 'Career Opportunities')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if not strip_tags(item):
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags(''.join(holder), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        structure = response.xpath(
            "//div[contains(@id, 'comp-') and not(contains(@id, 'comp-ik'))][last()]/*[contains(*//text(), 'Competencies')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if not strip_tags(item):
                break
            else:
                holder.append(item)
        if holder:
            course_item["courseStructure"] = strip_tags(''.join(holder), remove_all_tags=False,
                                                       remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        yield course_item
