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


class UoqSpiderSpider(scrapy.Spider):
    name = 'uoq_spider'
    allowed_domains = ['my.uq.edu.au', 'future-students.uq.edu.au', 'uq.edu.au']
    start_urls = ['https://future-students.uq.edu.au/study/programs']
    banned_urls = []
    courses = []
    institution = "The University of Queensland (UQ)"
    uidPrefix = "AU-UOQ-"

    campuses = {
        "Teaching Hospitals": "715",
        "Ipswich": "716",
        "Brisbane": "718",
        "Pharmacy Aust Cntr Excellence": "717",
        "Herston": "714",
        "Gatton": "713",
        "St Lucia": "711",
        "External": "712"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "masters": research_coursework,
        "bachelors": bachelor_honours,
        "doctor": "6",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        self.courses.extend(response.xpath("//div[contains(@class, 'tabs__content--active')]//div["
                                           "@role='article']//a/@href").getall())

        next_page = response.xpath("//div[contains(@class, 'tabs__content--active')]//a[@rel='next']/@href").get()

        if next_page:
            yield response.follow(next_page, callback=self.parse)

        for item in self.courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        degree = response.xpath("//h1/span/text()").get()
        if degree:
            degree = degree.strip()
        else:
            degree = ""
        study_field = response.xpath("//h1/text()").get()
        if study_field:
            study_field = study_field.strip()
        else:
            study_field = ""
        course_name = degree + " " + study_field
        course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//section[contains(@data-gtm-category, 'Program section')]/article/div").get()
        if overview:
            course_item["overview"] = strip_tags(overview, False)

        summary = response.xpath("//section[contains(@data-gtm-category, 'Program section')]/article/p/text()").getall()
        if summary:
            summary = [x.strip() for x in summary]
            summary = "".join(summary)
            course_item.set_summary(summary)

        cricos = response.xpath("//dt[contains(text(), 'CRICOS Code')]/following-sibling::dd/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_code = response.xpath("//dt[contains(text(), 'Program Code')]/following-sibling::dd/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        start = response.xpath("//dt[contains(text(), 'Start Semester')]/following-sibling::dd/text()").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        duration = response.xpath("//dt[contains(text(), 'Duration')]/following-sibling::dd/text()").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration,
                                       re.I | re.M | re.DOTALL)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if re.search("half year", duration, re.I):
                course_item["durationMinFull"] = 0.5
                course_item["teachingPeriod"] = 1

        fee = response.xpath("//dt[contains(text(), 'Fees')]/following-sibling::dd").get()
        if fee:
            fee = re.search("(?<=\$).*?(\d+)", fee, re.DOTALL | re.M)
            if fee:
                fee = fee.group()
                try:
                    course_item["internationalFeeAnnual"] = float(fee)
                    get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)
                except ValueError:
                    pass

        location = response.xpath("//dt[contains(text(), 'Location')]/following-sibling::dd/text()").get()
        if location:
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        career = response.xpath("//div[contains(*/text(), 'Career possibilities')]/following-sibling::*/*").getall()
        if career:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(career, False)

        learn = response.xpath("//div[contains(*/text(), 'Program highlights')]/following-sibling::div").get()
        if learn:
            course_item["whatLearn"] = strip_tags(learn, False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        if study_field:
            if re.search("/", study_field):
                course_item["doubleDegree"] = 1
                study_split = re.split("\s?/\s?", study_field.strip())
                course_item["rawStudyfield"] = [x.lower() for x in study_split]
                course_item["specificStudyField"] = "/".join(study_split)
                if study_field.count("Honours") == 1:
                    course_item["degreeType"] = "Bachelor"
                    course_item["canonicalGroup"] = "The Uni Guide"
                    course_item["group"] = 3

        if "courseCode" in course_item:
            course_item["uid"] = course_item["uid"] + "-" + course_item["courseCode"]

        yield course_item
