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


class CquSpiderSpider(scrapy.Spider):
    name = 'cqu_spider'
    allowed_domains = ['www.cqu.edu.au', 'cqu.edu.au']
    start_urls = ['https://www.cqu.edu.au/courses/find-a-course']
    banned_urls = []
    courses = []
    institution = "The University of Queensland (UQ)"
    uidPrefix = "AU-UOQ-"

    campuses = {
        "Bundaberg": "545",
        "Gladstone Marina": "568",
        "Rockhampton North": "566",
        "Mackay City": "543",
        "Rockhampton": "547",
        "Noosa": "549",
        "Perth": "558",
        "Sydney": "550",
        "Melbourne": "556",
        "Emerald": "548",
        "Townsville": "546",
        "Cairns": "542",
        "Brisbane": "551",
        "Adelaide": "553",
        "Rockhampton City": "544",
        "Mackay": "567"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "phd": "6",
        "advanced certificate": "7",
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
        courses = response.xpath("//div[@id='course_results']/div[@class='ct-course-card']//a["
                                 "@class='course-name']/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

        active_page = response.xpath("//ul[@class='pagination-list']/li[@class='pagination-list__item "
                                     "active']/a/span/text()").get()
        next_page = int(active_page) + 1
        next_xpath = "//ul[@class='pagination-list']//a[span/text()='" + str(next_page) + "']/@href"
        next_page_url = response.xpath(next_xpath).get()
        if next_page_url:
            yield response.follow(next_page_url, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//title/text()").get()
        if course_name:
            course_name = re.sub("- CQUniversity", "", course_name)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//h1[@itemprop='name']/text()").get()
        if course_code:
            course_code = re.findall(r"\b[0-9A-Z]+\b", course_code)
            if course_code:
                course_item["courseCode"] = course_code[0]

        if "courseCode" in course_item and "courseName" in course_item:
            course_item["uid"] = course_item["uid"] + "-" + course_item["courseCode"]

        overview = response.xpath("//label[contains(span/text(), 'Course Details')]/following-sibling::*").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            course_item["overview"] = strip_tags("".join(overview), False)

        duration = response.xpath("//span[@class='course-info-highlight'][contains(text(), "
                                  "'DURATION')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
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
        if "durationMinFull" not in course_item:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration,
                                       re.I | re.M | re.DOTALL)
            if duration_full:
                if len(duration_full) == 1:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full) == 2:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    self.get_period(duration_full[1][1].lower(), course_item)

        location = response.xpath("//span[@class='course-info-highlight'][contains(text(), "
                                  "'AVAILABILITY')]/following-sibling::*").get()
        if location:
            campus_holder = []
            for campus in self.campuses:
                if campus == "Rockhampton":
                    if re.search("Rockhampton(?!\s(City|North))", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif campus == "Mackay":
                    if re.search("Mackay(?!\sCity)", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        study = response.xpath("//span[@class='course-info-highlight'][contains(text(), 'STUDY "
                               "MODES')]/following-sibling::*").get()
        study_holder = []
        if study:
            if re.search(r"online", study, re.M | re.I):
                study_holder.append("Online")
        if "campusNID" in course_item:
            study_holder.append("In Person")
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        score = response.xpath("//span[@class='course-info-highlight'][contains(text(), 'RANK CUT "
                               "OFF')]/following-sibling::*").get()
        if score:
            score = re.findall("ATAR:\s?(\d*\.?\d+)", score, re.I | re.M)
            if score:
                try:
                    course_item["guaranteedEntryScore"] = float(score[0])
                except ValueError:
                    pass

        cricos = response.xpath("//span[@class='course-info-highlight'][contains(text(), "
                                "'CRICOS')]/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        entry = response.xpath("//label[contains(span/text(), 'Entry Requirements')]/following-sibling::*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags("".join(entry), False)

        career = response.xpath("//label[contains(span/text(), 'Career Opportunities and "
                                "Outcomes')]/following-sibling::*").getall()
        if career:
            course_item["careerPathways"] = strip_tags("".join(career), False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        if "courseName" in course_item:
            if course_item["courseName"] in ["BAS Agent Registration Skill Set",
                                             "Team Leader Skill Set",
                                             "Accounting Principles Skills Set",
                                             "Enterprise Trainer (Presenting)"]:
                course_item["degreeType"] = "4"

        yield course_item
