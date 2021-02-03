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


class TopSpiderSpider(scrapy.Spider):
    name = 'top_spider'
    start_urls = ['https://www.top.edu.au/school-of-business/undergraduate-programs',
                  'https://www.top.edu.au/school-of-business/postgraduate-programs']
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
        courses = response.xpath("//div[@id='main-content']/ul/li//a/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
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

        cricos = response.xpath("//td[contains(strong/text(), 'CRICOS')]/following-sibling::*").get()
        if not cricos:
            cricos = response.xpath("//strong[contains(text(), 'CRICOS')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        duration = response.xpath("//td[contains(strong/text(), 'Duration')]/following-sibling::*").get()
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
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        overview = response.xpath("//td[contains(strong/text(), 'Program Overview')]/following-sibling::*").get()
        if not overview:
            overview = response.xpath("//td[contains(span/strong/text(), 'Program Overview')]/following-sibling::*").get()
        if not overview:
            overview = response.xpath("//td[contains(strong/span/text(), 'Program Overview')]/following-sibling::*").get()
        if not overview:
            overview = response.xpath("//td[contains(span/strong/em/text(), 'Program Overview')]/following-sibling::*").get()
        if not overview:
            course_item.add_flag("overview", "no overview found: " + response.request.url)
        if overview:
            course_item['overview'] = strip_tags(overview, remove_all_tags=False, remove_hyperlinks=True)
            course_item.set_summary(strip_tags(overview))

        career = response.xpath("//td[contains(strong/text(), 'Career Options')]/following-sibling::*").get()
        if career:
            course_item["careerPathways"] = strip_tags(career, remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath("//td[contains(strong/text(), 'Credit arrangement')]/following-sibling::*").get()
        if credit:
            course_item["creditTransfer"] = strip_tags(credit, remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//td[contains(strong/text(), 'Entry Requirements')]/following-sibling::*").get()
        if entry:
            course_item["entryRequirements"] = strip_tags(entry, remove_all_tags=False, remove_hyperlinks=True)

        study = response.xpath("//td[contains(strong/text(), 'Delivery Site')]/following-sibling::*").get()
        campus_holder = []
        study_holder = []
        if study:
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

        learn = response.xpath("//td[contains(strong/text(), 'Learning Outcomes')]/following-sibling::*").get()
        if learn:
            course_item["whatLearn"] = strip_tags(learn, remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath("//td[contains(strong/text(), 'Course Structure')]/following-sibling::*").get()
        if not structure:
            structure = response.xpath("//td[contains(strong/span/text(), 'Course Structure')]/following-sibling::*").get()
        if structure:
            course_item["courseStructure"] = strip_tags(structure, remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item



