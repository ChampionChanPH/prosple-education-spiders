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


class CmuSpiderSpider(scrapy.Spider):
    name = 'cmu_spider'
    allowed_domains = ['www.australia.cmu.edu', 'australia.cmu.edu']
    start_urls = ['https://www.australia.cmu.edu/study']
    banned_urls = []
    courses = []
    institution = "The University of Queensland (UQ)"
    uidPrefix = "AU-UOQ-"

    campuses = {
        "Adelaide": "512",
        "Hybrid": "514",
        "Pittsburgh": "513"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "advanced certificate": "4",
        "certificate": "4",
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
        courses = response.xpath("//div[@class='menuitem']//li/a/@href").getall()

        courses = ["https://www.australia.cmu.edu/study/public-policy-and-management/msppm-12-month-program",
                   "https://www.australia.cmu.edu/study/business-intelligence-data-analytics/graduate-cert-in-bida",
                   "https://www.australia.cmu.edu/study/public-policy-and-management/msppm-public-private-partnerships"]
        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h2/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[contains(@class, 'content__block')][1]/*").getall()
        if overview:
            if len(overview[0]) < 35:
                course_item.set_summary(strip_tags(overview[1]))
            else:
                course_item.set_summary(strip_tags(overview[0]))
            holder = []
            for index, item in enumerate(overview):
                if index != 0 and not re.search("^<p", item):
                    break
                else:
                    holder.append(item)
            if holder:
                course_item["overview"] = strip_tags("".join(holder), False)

        cricos = response.xpath("//p[contains(text(), 'CRICOS:')]").getall()
        if cricos:
            cricos = "".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        duration = response.xpath("//td[text() = 'Duration']/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s"
                                       "?\sfull.time)", duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*?\.?\d*?)\s?t?o?\s?(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day)s?\spart.time)", duration,
                                       re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][2].lower(), course_item)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][2].lower()] == course_item["teachingPeriod"]:
                    if duration_part[0][0] == "":
                        course_item["durationMinPart"] = float(duration_part[0][1])
                    else:
                        course_item["durationMinPart"] = float(duration_part[0][0])
                        course_item["durationMaxPart"] = float(duration_part[0][1])
                else:
                    if duration_part[0][0] == "":
                        course_item["durationMinPart"] = float(duration_part[0][1]) * course_item["teachingPeriod"] \
                                                         / self.teaching_periods[duration_part[0][2].lower()]
                    else:
                        course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                         / self.teaching_periods[duration_part[0][2].lower()]
                        course_item["durationMaxPart"] = float(duration_part[0][1]) * course_item["teachingPeriod"] \
                                                         / self.teaching_periods[duration_part[0][2].lower()]
        if "durationMinFull" not in course_item:
            duration_full = re.findall("(\d*\.?\d+)(?=-(year|month|semester|trimester|quarter|week|day))", duration,
                                       re.I | re.M | re.DOTALL)
            if duration_full:
                if len(duration_full) == 1:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full) == 2:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    self.get_period(duration_full[1][1].lower(), course_item)

        course_structure = response.xpath("//h2[text()='Degree Structure']/following-sibling::*").getall()
        if not course_structure:
            course_structure = response.xpath("//h2[text()='Program Structure']/following-sibling::*").getall()
        if course_structure:
            holder = []
            for item in course_structure:
                if re.search("^<h2", item):
                    break
                else:
                    holder.append(item)
            if holder:
                course_item["courseStructure"] = strip_tags("".join(holder), False)

        learn = response.xpath("//h2[text()='Learning outcomes']/following-sibling::*").getall()
        if learn:
            holder = []
            for item in learn:
                if re.search("^<h2", item):
                    break
                else:
                    holder.append(item)
            if holder:
                course_item["whatLearn"] = strip_tags("".join(holder), False)

        entry = response.xpath("//h2[text()='Entry Requirements']/following-sibling::*").getall()
        if entry:
            holder = []
            for item in entry:
                if re.search("^<h2", item):
                    break
                else:
                    holder.append(item)
            if holder:
                course_item["entryRequirements"] = strip_tags("".join(holder), False)

        career = response.xpath("//h2[text()='Internships and Career Outcomes']/following-sibling::*").getall()
        if career:
            holder = []
            for item in career:
                if re.search("^<h2", item):
                    break
                else:
                    holder.append(item)
            if holder:
                course_item["careerPathways"] = strip_tags("".join(holder), False)

        location = response.xpath("//td[text() = 'Location']/following-sibling::*").get()
        if location:
            study_holder = []
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)
                study_holder.append("In Person")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        period = response.xpath("//td[text() = 'Intakes']/following-sibling::*").get()
        if period:
            start_holder = []
            for month in self.months:
                if re.search(month, period, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item
