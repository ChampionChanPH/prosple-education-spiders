# -*- coding: utf-8 -*-
# by Christian Anasco
# having difficulties getting the annual fee for courses

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


class FuaSpiderSpider(scrapy.Spider):
    name = 'fua_spider'
    allowed_domains = ['study.federation.edu.au', 'federation.edu.au']
    start_urls = ['https://study.federation.edu.au/search/?modes=domestic']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    courses = []
    institution = "Federation University Australia"
    uidPrefix = "AU-FUA-"

    campuses = {
        "On-line Learning": "11707",
        "Gippsland - Churchill": "11716",
        "Broadmeadows": "607",
        "Flexible Delivery - Wimmera": "606",
        "Chadstone / Ballarat": "605",
        "Flexible Delivery - Berwick": "604",
        "Flexible Delivery - Ballarat": "603",
        "Horsham and Stawell": "602",
        "Ballarat - Camp St": "601",
        "Gillies Street": "600",
        "External": "599",
        "Flexible Delivery - Gippsland": "598",
        "Workplace - Other Victoria": "597",
        "Workplace - Ballarat": "596",
        "Ballarat": "590",
        "Mt Rowan - Rural Skills Centre": "595",
        "Wimmera - Horsham": "594",
        "Berwick": "593",
        "Ballarat - Mt Helen": "592",
        "Ballarat - SMB": "591",
        "Brisbane": "51245"
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
        "undergraduate certificate": "4",
        "vcal - victorian certificate": "4",
        "victorian certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "course": "13",
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

    sem = {
        "1": "03",
        "2": "07"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.sub_parse, args={'wait': 20})

    def sub_parse(self, response):
        courses = response.xpath(
            "//div[contains(@id, 'degree-list-item')]//a[contains(@class, 'btn-readMore')]/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//div[@id='course-title-header']/h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@id='course-outline-expand']/div/div/*").getall()
        if not overview:
            overview = response.xpath("//div[@id='course-outline-expand']/div/*").getall()
        if overview:
            overview = [x for x in overview if strip_tags(x).strip() != '']
            if not overview:
                overview = response.xpath("//div[@id='course-outline-expand']/div/*").getall()
                overview = [x for x in overview if strip_tags(x).strip() != '']
            course_item.set_summary(strip_tags(overview[0]))
            course_item["overview"] = strip_tags(''.join(overview), False)

        # intake = response.xpath("//*[@ng-bind-html='prg.program.commences']/text()").get()
        # if intake:
        #     start_holder = []
        #     for item in self.sem:
        #         if re.search(item, intake, re.I | re.M):
        #             start_holder.append(self.sem[item])
        #     if start_holder:
        #         course_item["startMonths"] = "|".join(start_holder)

        location = response.xpath("//*[@id='locations-and-semesters']").get()
        if location:
            campus_holder = []
            for campus in self.campuses:
                if campus == "Ballarat":
                    if re.search("Ballarat(?!\s-)", location, re.I | re.M) and \
                            re.search("(?<!-\s)Ballarat", location, re.I | re.M) and \
                            re.search("(?<!/\s)Ballarat", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)
            study_holder = set()
            if len(campus_holder) == 1:
                if "11707" in campus_holder:
                    study_holder.add("Online")
                else:
                    study_holder.add("In Person")
            if len(campus_holder) > 1:
                if "11707" in campus_holder:
                    study_holder.add("Online")
                study_holder.add("In Person")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        duration = response.xpath("//*[@id='course-overview-length']").get()
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
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
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

        cricos = response.xpath("//p[contains(*/text(), 'CRICOS')]").getall()
        if cricos:
            cricos = ''.join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ', '.join(cricos)
                course_item["internationalApps"] = 1

        career = response.xpath("//div[@id='course-careers-expand']/*/*").getall()
        if career:
            career = [x for x in career if strip_tags(x).strip() != '']
            course_item["careerPathways"] = strip_tags("".join(career), False)

        credit = response.xpath("//div[@id='course-recognition_of_prior_learning-expand']/*").getall()
        if credit:
            credit = [x for x in credit if strip_tags(x).strip() != '']
            course_item["creditTransfer"] = strip_tags("".join(credit), False)

        code = re.findall(r"/([0-9A-Z.]+)\b", course_item["sourceURL"])
        if code:
            course_item["uid"] = course_item["uid"] + "-" + code[0]

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        yield course_item
