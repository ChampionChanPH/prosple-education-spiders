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


class ScuonlineSpiderSpider(scrapy.Spider):
    name = 'scuonline_spider'
    start_urls = ['https://online.scu.edu.au/courses/']
    institution = "Southern Cross University (SCU)"
    uidPrefix = "AU-SCU-ON-"

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
        "vcal in victorian certificate": "9",
        "vcal in": "9",
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
        "Melbourne": "701",
        "Lismore": "695",
        "Gold Coast": "696",
        "Perth": "700",
        "Sydney": "699",
        "Tweed Heads": "698",
        "Coffs Harbour": "697",
        "National Marine Science Centre": "694",
    }

    key_dates = {
        "1": "03",
        "2": "07",
        "3": "11"
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
        courses = response.xpath("//a[text()='Course details']/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//span[@id='system-breadcrumb']/following-sibling::*/*[last()]/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview1 = response.xpath("//div[*/*/*/*/text()='Quick facts']/following-sibling::*//h2").get()
        holder = []
        if overview1:
            holder.append(overview1)
            overview2 = response.xpath(
                "//div[*/*/*/*/text()='Quick facts']/following-sibling::*//h2/following-sibling::*").getall()
            if overview2:
                holder.extend(overview2)
                summary = [strip_tags(x) for x in overview2]
                course_item.set_summary(' '.join(summary))
        if holder:
            course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False)

        learn = response.xpath("//div[@class='learning-outcomes right']/*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), remove_all_tags=False)

        entry = response.xpath(
            "//*[contains(@class, 'tab-pane')]/*[contains(@class, 'paragraph--type--bp-simple')]/*/*/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//div[@class='vp-header'][*/text()='Duration']/following-sibling::*").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?,?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?,?\s+?part)",
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

        intake = response.xpath("//div[@class='vp-header'][*/text()='Intakes']/following-sibling::*").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        total_unit = response.xpath("//div[@class='vp-header'][*/text()='Units']/following-sibling::*").get()
        if total_unit:
            total_unit = re.findall('\d+', total_unit)
            total_unit = [float(x) for x in total_unit]
            if total_unit:
                total_unit = max(total_unit)

        fee = response.xpath("//div[@class='vp-header'][*/text()='Fees']/following-sibling::*").get()
        if fee:
            fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", fee, re.M)
            fee = [float(''.join(x)) for x in fee]
            if fee and total_unit:
                course_item["domesticFeeTotal"] = max(fee) * total_unit
                course_item["internationalFeeTotal"] = max(fee) * total_unit
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        career = response.xpath("//ul[@class='blue-bullets']/*").getall()
        if career:
            course_item['careerPathways'] = '<ul>' + ''.join(career) + '</ul>'

        course_item['modeOfStudy'] = 'Online'

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
