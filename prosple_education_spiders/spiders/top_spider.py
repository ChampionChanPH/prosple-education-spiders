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


class TopSpiderSpider(scrapy.Spider):
    name = 'top_spider'
    start_urls = ['https://www.imc.edu.au/future-students/course-information/undergraduate-courses',
                  'https://www.imc.edu.au/future-students/course-information/postgraduate-courses']
    banned_urls = ['/school-of-business/postgraduate-programs/graduate-diploma-of-public-relations-and-marketing'
                   '/graduate-diploma-of-public-relations-and-marketing',
                   '/school-of-business/postgraduate-programs/master-of-professional-accounting-and-business/master'
                   '-of-professional-accounting-and-business',
                   '/school-of-business/postgraduate-programs/master-of-marketing-and-public-relations--/master-of'
                   '-marketing-and-public-relations',
                   '/school-of-business/postgraduate-programs/pathway-to-the-university-of-newcastle/pathway-to-the'
                   '-university-of-newcastle']
    institution = "Australian National Institute of Management and Commerce (IMC)"
    uidPrefix = "AU-TOP-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Hobart": "43956",
        "Eveleigh": "43955"
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
        courses = response.xpath(
            "//div[@class='page-header']/following-sibling::p/a/@href").getall()
        if not courses:
            courses = response.xpath(
                "//div[contains(@class, 'panel-default')]/div[contains(@class, 'panel-body')]//a/@href").getall()

        for item in courses:
            # if item not in self.banned_urls:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        cricos = response.xpath(
            "//small[contains(text(), 'CRICOS')]/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        overview = response.xpath(
            "//div[h4/text()='PROGRAM OVERVIEW']/following-sibling::*[1]/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath(
            "//div[h4/text()='DURATION']/following-sibling::*/*").getall()
        if duration:
            duration = ''.join(duration)
            duration = duration.replace("term", "semester")
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

        career = response.xpath(
            "//div[h4/text()='PATHWAY TO EMPLOYMENT / FURTHER STUDY']/following-sibling::*/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(
                "".join(career), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath(
            "//div[h4/text()='CREDIT ARRANGEMENT']/following-sibling::*/*").getall()
        if credit:
            course_item["creditTransfer"] = strip_tags(
                "".join(credit), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//div[h4/text()='ENTRY REQUIREMENTS']/following-sibling::*/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(
                "".join(entry), remove_all_tags=False, remove_hyperlinks=True)

        study = response.xpath(
            "//div[h4/text()='DELIVERY SITE']/following-sibling::*/*").getall()
        campus_holder = []
        study_holder = []
        if study:
            study = "".join(study)
            if re.search('on campus', study, re.M | re.I):
                study_holder.append("In Person")
            if re.search('online', study, re.M | re.I):
                study_holder.append("Online")
            for campus in self.campuses:
                if re.search(campus, study, re.I):
                    campus_holder.append(self.campuses[campus])
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        # learn = response.xpath(
        #     "//td[contains(strong/text(), 'Learning Outcomes')]/following-sibling::*").get()
        # if learn:
        #     course_item["whatLearn"] = strip_tags(
        #         learn, remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//div[h4/text()='COURSE STRUCTURE']/following-sibling::*/*").getall()
        if structure:
            course_item["courseStructure"] = strip_tags(
                "".join(structure), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item
