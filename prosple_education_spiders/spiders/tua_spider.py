# -*- coding: utf-8 -*-
# by Christian Anasco
# Check key date section to get exceptions in "startMonths"
# Key date link: https://www.torrens.edu.au/apply-online/key-dates

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


class TuaSpiderSpider(scrapy.Spider):
    name = 'tua_spider'
    allowed_domains = ['torrens.edu.au', 'www.torrens.edu.au']
    start_urls = ['https://www.torrens.edu.au/courses']
    institution = "Torrens University Australia"
    uidPrefix = "AU-TUA-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "mba": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Gotha Street Campus, Brisbane": "43385",
        "Torrens University Language Centre, Brisbane": "43384",
        "Fortitude Valley Campus, Brisbane": "720",
        "Torrens University Language Centre, Melbourne": "43383",
        "Fitzroy Campus, Melbourne": "43382",
        "Flinders Street Campus, Melbourne": "722",
        "Leura Campus, Sydney": "43374",
        "Kent Street Campus, Sydney": "43373",
        "Torrens University Language Centre, Sydney": "43372",
        "Town Hall Campus, Sydney": "43371",
        "Pyrmont Campus, Sydney": "11784",
        "The Rocks Campus, Sydney": "723",
        "Ultimo Campus, Sydney": "11788",
        "Wakefield Street Campus, Adelaide": "719"
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
        categories = response.xpath("//div[contains(@class, 'faculty-group')]//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.css("div.border.black-border")

        for item in courses:
            fields = {}

            learn = item.css("div.col-12.col-md-4.pb-3").get()
            if learn is not None:
                fields["learn"] = re.sub(r"key study outcomes", "Key Study Outcomes", learn, re.M)
            fields["location"] = item.css("p.pb-0.mb-2").get()
            course_link = item.css("a.view-course-button::attr(href)").get()
            yield response.follow(course_link, callback=self.course_parse, meta={'fields': fields})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        cricos = response.xpath("//div[contains(text(), 'Cricos Code')]/text()").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M | re.I)
            if len(cricos) > 0:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        overview = response.xpath("//h2/following-sibling::*").getall()
        if len(overview) > 0:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview.strip(), False)

        duration_full = response.xpath("//div[i[contains(@class, 'ion-record')]]/following-sibling::*").get()
        duration_part = response.xpath("//div[i[contains(@class, 'ion-contrast')]]/following-sibling::*").get()
        if duration_full is not None:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration_full, re.M)
        if duration_part is not None:
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration_part, re.M)
        if duration_full is not None:
            if len(duration_full) == 0 and len(duration_part) > 0:
                if len(duration_part) == 1:
                    self.get_period(duration_part[0][1], course_item)
                if len(duration_part) == 2:
                    self.get_period(duration_part[1][1], course_item)
            else:
                if len(duration_full) == 1:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1], course_item)
                elif len(duration_full) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    course_item["durationMaxFull"] = float(duration_full[1][0])
                    self.get_period(duration_full[1][1], course_item)
        if duration_part is not None:
            if len(duration_part) == 1:
                if self.teaching_periods[duration_part[0][1]] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1]]
            elif len(duration_part) == 2:
                if self.teaching_periods[duration_part[1][1]] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                    course_item["durationMaxPart"] = float(duration_part[1][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1]]
                    course_item["durationMaxPart"] = float(duration_part[1][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[1][1]]

        course_item["whatLearn"] = response.meta["fields"]["learn"]

        location = response.meta["fields"]["location"]

        check_online = response.xpath("//h3[contains(text(), 'Where can I study')]/following-sibling::div").get()
        campus_holder = []
        study_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if check_online is not None:
            if re.search("online", location, re.I | re.M):
                study_holder.append("Online")
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)
            study_holder.append("In Person")
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)

        if course_item["courseName"] == "Bachelor of Nursing":
            course_item["startMonths"] = "02|09"
        elif course_item["courseName"] == "Master of Business Administration, Innovation and Leadership (Partnership " \
                                          "with Ducere)":
            course_item["startMonths"] = "03|08|09"
        elif course_item["courseName"] in ["Bachelor of Applied Entrepreneurship (Partnership with Ducere)",
                                           "Bachelor of Applied Business, Marketing (Partnership With Ducere)",
                                           "Bachelor of Applied Business, Management (Partnership with Ducere)"]:
            course_item["startMonths"] = "01|04|07|10"
        elif course_item["courseName"] == "Diploma of Travel And Tourism (In partnership with Flight Centre Travel " \
                                          "Academy)":
            course_item["startMonths"] = "01|02|03|04|05|06|07"
        else:
            course_item["startMonths"] = "02|06|09"

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "Of"])

        yield course_item
