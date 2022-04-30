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


class UocSpiderSpider(scrapy.Spider):
    name = 'uoc_spider'
    start_urls = [
        "https://www.canberra.edu.au/future-students/study-at-uc/find-a-course/view-all-courses"]
    institution = "University of Canberra"
    uidPrefix = "AU-UOC-"
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        # One course "Honours in Information Sciences" not captured, manually
        "bachelor": bachelor_honours,
        # updated
        "doctor": "6",
        "professional doctorate": "6",
        "certificate": "4",
        "undergraduate certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "university foundation studies": "13",
        # "University of Canberra International Foundation Studies" not captured, manually
        "non-award": "13",
        # updated
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
        "Singapore": "738",
        "Canberra": "735",
        "Sydney": "737"
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
        yield SplashRequest(response.request.url, callback=self.splash_parse, args={'wait': 20})

    def splash_parse(self, response):
        courses = response.xpath("//td/a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@id='page-title']/text()").get()
        if re.search("\(", course_name):
            course_name, course_code = re.findall(
                "(.*) \((.*)\)$", course_name.strip(), re.I | re.M)[0]
            course_item.set_course_name(course_name.strip(), self.uidPrefix)
            course_item["courseCode"] = course_code
        else:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//div[@class='introduction']/div/*").getall()
        if not overview:
            overview = response.xpath(
                "//div[@class='introduction']/node()").getall()
            overview = [x for x in overview if strip_tags(x) != ""]
        if not overview:
            overview = response.xpath("//div[@class='introduction']").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search("^<(p|o|u|d)", item) and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath(
            "//div[@class='introduction']//h4[contains(text(), 'and you will:')]/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(learn):
            if not re.search("^<(p|o|u|d)", item) and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            course_item["whatLearn"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//div[@class='introduction']//h4[text()='Career opportunities']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(career):
            if not re.search("^<(p|o|u|d)", item) and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        table_headers = response.xpath(
            "//div[@class='course-details section']//table[@id='custom-table-css']/thead//th").getall()
        table_contents = response.xpath(
            "//div[@class='course-details section']//table[@id='custom-table-css']/tbody//td").getall()

        if 'CRICOS code' in table_headers:
            cricos = table_contents[table_headers.index('CRICOS code')]
            if cricos:
                cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
                if cricos:
                    course_item["cricosCode"] = ", ".join(cricos)

        if 'Location' in table_headers:
            location = table_contents[table_headers.index('Location')]
            campus_holder = set()
            if location:
                for campus in self.campuses:
                    if re.search(campus, location, re.I):
                        campus_holder.add(self.campuses[campus])
            if campus_holder:
                course_item['campusNID'] = '|'.join(campus_holder)

        if 'Selection rank ' in table_headers:
            atar = table_contents[table_headers.index('Selection rank ')]
            if atar:
                atar = re.findall("\d{2,3}", atar, re.M)
                if atar:
                    course_item["cricosCode"] = float(atar[0])

        if 'Duration' in table_headers:
            duration = table_contents[table_headers.index('Duration')]
            if duration:
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
                        course_item["durationMinPart"] = float(
                            duration_part[0][0])
                    else:
                        course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                            / self.teaching_periods[duration_part[0][1].lower()]
                if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                    duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                               duration, re.I | re.M | re.DOTALL)
                    if duration_full:
                        course_item["durationMinFull"] = float(
                            duration_full[0][0])
                        self.get_period(
                            duration_full[0][1].lower(), course_item)
                        # if len(duration_full) == 1:
                        #     course_item["durationMinFull"] = float(duration_full[0][0])
                        #     self.get_period(duration_full[0][1].lower(), course_item)
                        # if len(duration_full) == 2:
                        #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        #     self.get_period(duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              "and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
