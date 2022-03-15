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
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class EitSpiderSpider(scrapy.Spider):
    name = 'eit_spider'
    start_urls = [
        "https://www.eit.edu.au/courses/online-master-of-engineering-electrical-systems/",
        "https://www.eit.edu.au/courses/online-master-of-engineering-industrial-automation/",
        "https://www.eit.edu.au/courses/online-master-of-engineering-civil-structural/",
        "https://www.eit.edu.au/courses/online-master-of-engineering-mechanical/",
        "https://www.eit.edu.au/courses/doctor-of-engineering/"
    ]
    institution = "Engineering Institute of Technology"
    uidPrefix = "AU-EIT-"

    campuses = {

    }

    degrees = {
        "master": research_coursework,
        "doctor": "6",
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
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1").get()
        if course_name:
            new_name = re.sub("Online - ", "", course_name)
            course_item.set_course_name(strip_tags(new_name), self.uidPrefix)
            course_item["courseName"] = strip_tags(course_name)

        overview = response.xpath(
            "//div[@id='eit_course_code']/following-sibling::*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        course_code = response.xpath("//div[@id='eit_course_code']").get()
        if course_code:
            course_item["courseCode"] = strip_tags(course_code)

        duration = response.xpath(
            "//div[@class='glance__title' and text()='Duration']/following-sibling::*").get()
        if duration:
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
                        course_item["durationMinFull"] = float(
                            duration_full[0][0])
                        self.get_period(
                            duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(
                            duration_full[1][1].lower(), course_item)

        study = response.xpath(
            "//div[@class='glance__title' and text()='Study Mode']/following-sibling::*").get()
        study_holder = set()
        if study:
            if re.search('blended', study, re.I | re.M):
                study_holder.add('Online')
                study_holder.add('In Person')
            if re.search('online', study, re.I | re.M | re.DOTALL):
                study_holder.add('Online')
            if re.search('on.campus', study, re.I | re.M | re.DOTALL):
                study_holder.add('In Person')
            if re.search('face', study, re.I | re.M):
                study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        start = response.xpath(
            "//div[@class='glance__title' and text()='Intakes']/following-sibling::*").get()
        if start:
            holder = []
            for item in self.months:
                if re.search(item, start, re.I | re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        structure = response.xpath(
            "//div[contains(@id, 'ProgramStructure')]/*/*").getall()
        holder = []
        if structure:
            for item in structure:
                if re.search("^(p|u|o)", item):
                    holder.append(item)
                else:
                    break
        if holder:
            course_item["courseStructure"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        outcome = response.xpath(
            "//div[contains(@id, 'ProgramLearningOutcomes')]/*/*").getall()
        if outcome:
            course_item["whatLearn"] = strip_tags(
                ''.join(outcome), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//div[contains(@id, 'EntryRequirements')]/*/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//div[contains(@id, 'PotentialJobOutcomes')]/*/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
