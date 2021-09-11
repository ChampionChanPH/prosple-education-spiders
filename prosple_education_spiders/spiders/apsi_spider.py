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


class ApsiSpiderSpider(scrapy.Spider):
    name = 'apsi_spider'
    allowed_domains = ['a']
    start_urls = [
        "https://www.apsi.edu.au/courses/commercial-cookery/certificate-iii-in-commercial-cookery/",
        "https://www.apsi.edu.au/courses/health-care-training/certificate-iii-in-individual-support/",
        "https://www.apsi.edu.au/courses/patisserie/certificate-iii-in-patisserie/",
        "https://www.apsi.edu.au/courses/health-care-training/certificate-iv-in-ageing-support/",
        "https://www.apsi.edu.au/courses/commercial-cookery/certificate-iv-in-commercial-cookery/",
        "https://www.apsi.edu.au/courses/patisserie/certificate-iv-patisserie",
        "https://www.apsi.edu.au/courses/business-management/diploma-of-business/",
        "https://www.apsi.edu.au/courses/health-care-training/diploma-of-community-services/",
        "https://www.apsi.edu.au/courses/hospitality-courses/diploma-of-hospitality/",
        "https://www.apsi.edu.au/courses/business-management/diploma-leadership-management/",
        "https://www.apsi.edu.au/courses/business-management/advanced-diploma-business/",
        "https://www.apsi.edu.au/courses/hospitality-courses/advanced-diploma-of-hospitality/",
        "https://www.apsi.edu.au/courses/business-management/advanced-diploma-leadership-and-management/"
    ]
    institution = "Australian Professional Skills Institute (APSI)"
    uidPrefix = "AU-APSI-"

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
        "Geelong City Campus": "58312",
        "East Geelong Campus": "58313",
        "Werribee": "58314",
        "Hoppers Crossing Trades Campus": "58314",
        "Colac Trade Training Centre": "58315",
        "Workplace": "58316",
        "Off Campus": "58316",
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

    courses = {

    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//*[@class='entry-title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[text()='Course Description']/following-sibling::*").getall()
        holder = []
        for item in overview:
            if re.search("^<(p|u|o)", item):
                holder.append(item)
            else:
                break
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(' '.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//*[contains(text(), 'Relevant Job Roles') or contains(text(), 'Career "
                                "outcomes')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if re.search("^<(p|u|o)", item):
                holder.append(item)
            else:
                break
        if holder:
            course_item['careerPathways'] = strip_tags(' '.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath(
            "//*[@class='et_pb_toggle_title'][text()='Course Duration']/following-sibling::*").getall()
        if duration:
            duration = '|'.join(duration)
            duration_full = re.findall("full.time.(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("part.time.(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
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
                                           duration,
                                           re.I | re.M | re.DOTALL)
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

        intake = response.xpath("//*[@class='et_pb_toggle_title'][text()='Intake Dates']/following-sibling::*").getall()
        if intake:
            intake = "|".join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        delivery = response.xpath(
            "//*[@class='et_pb_toggle_title'][text()='Mode of Delivery']/following-sibling::*").getall()
        study_holder = set()
        if delivery:
            delivery = "|".join(delivery)
        if re.search('(face|delivery|workplace)', delivery, re.I):
            study_holder.add('In Person')
        if re.search('online', delivery, re.I):
            study_holder.add('Online')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        course_item["campusNID"] = "30898"

        entry = response.xpath("//*[@class='et_pb_toggle_title'][text()='Admission Requirements' or text()='Entry "
                               "Requirements']/following-sibling::*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(' '.join(entry), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        credit = response.xpath("//*[@class='et_pb_toggle_title'][contains(text(), 'Recognition of Prior "
                                "Learning')]/following-sibling::*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(' '.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath("//*[contains(text(), 'CRICOS Course Code')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ', '.join(cricos)
                course_item['internationalApps'] = 1
                course_item['internationalApplyURL'] = response.request.url

        course_code = response.xpath("//*[contains(text(), 'VET National Code')]/text()").get()
        if course_code:
            course_code = re.findall("[A-Z]+[0-9]+", course_code, re.M)
            if course_code:
                course_item['courseCode'] = ', '.join(course_code)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 23
        course_item['canonicalGroup'] = 'StudyPerth'

        yield course_item
