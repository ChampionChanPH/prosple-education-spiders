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


class KaiSpiderSpider(scrapy.Spider):
    name = 'kai_spider'
    allowed_domains = ['www.kangan.edu.au', 'kangan.edu.au']
    start_urls = ['https://www.kangan.edu.au/courses/tafe-courses/browse-for-courses']
    institution = "Kangan Institute"
    uidPrefix = "AU-KAI-"

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
        "Online": "56874"
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
        courses = response.xpath("//div[@id='divtab2']//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//*[@class='h2_text']/text()").get()
        if course_name:
            course_item.set_course_name(make_proper(course_name.strip()), self.uidPrefix)

        course_code = response.xpath(
            "//div[contains(text(), 'Course Code')]/following-sibling::*[last()]/*/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        overview = response.xpath(
            "//p[@class='title_txt'][*/text()='Course Overview']/following-sibling::*/*/*").getall()
        holder = []
        for item in overview:
            if re.search('Click here for course modules', item, re.I | re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item.set_summary(strip_tags(holder[0]))
            course_item["overview"] = strip_tags(''.join(holder), False)

        career = response.xpath(
            "//*[contains(*/text(), 'What employment opportunities will I have')]/following-sibling::*/*").getall()
        holder = []
        for item in career:
            if re.search('lblquestion', item, re.I | re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags(''.join(holder), False)

        entry = response.xpath("//*[contains(*/text(), 'Can I apply')]/following-sibling::*/*").getall()
        holder = []
        for item in entry:
            if re.search('lblquestion', item, re.I | re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["entryRequirements"] = strip_tags(''.join(holder), False)

        apply = response.xpath("//*[contains(*/text(), 'How do I apply')]/following-sibling::*/*").getall()
        holder = []
        for item in apply:
            if re.search('lblquestion', item, re.I | re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["howToApply"] = strip_tags(''.join(holder), False)

        location = response.xpath("//div[contains(text(), 'Campus')]/following-sibling::*[last()]/*/text()").get()
        if location:
            course_item['campusNID'] = location

        duration = response.xpath(
            "//div[contains(text(), 'Course Length')]/following-sibling::*[last()]/*/text()").get()
        if duration:
            duration_full = re.findall("(?<=full.time\()(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(?<=part.time.day\()(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
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

        intake = response.xpath("//td[contains(text(), 'Start Date') or contains(*/text(), 'Start "
                                "Date')]/following-sibling::*").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        yield course_item
