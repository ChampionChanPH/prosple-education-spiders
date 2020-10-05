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


class CitSpiderSpider(scrapy.Spider):
    name = 'cit_spider'
    start_urls = ['https://cit.edu.au/courses']
    institution = "	Canberra Institute of Technology (CIT)"
    uidPrefix = "AU-CIT-"

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
        "CIT Bruce": "55522",
        "CIT Fyshwick": "55523",
        "CIT Gungahlin": "55524",
        "CIT Reid": "55525",
        "CIT Tuggeranong": "55526"
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
        categories = response.xpath("//div[@class='entry']/a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub_categories = response.xpath("//article[@class='post add']//a/@href").getall()
        sub_categories = set(sub_categories)

        for item in sub_categories:
            yield response.follow(item, callback=self.list_parse)

    def list_parse(self, response):
        courses = response.xpath("//table[@class='course-data']//td/a/@href").getall()
        courses = set(courses)

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//div[contains(@class, 'information-box')]//span").get()
        if course_name:
            course_name = re.sub('[0-9A-Z]{2,}$', '', course_name)
            course_item.set_course_name(strip_tags(course_name).strip(), self.uidPrefix)

        overview = response.xpath("//h2[@id='overview']/following-sibling::*").get()
        if overview:
            course_item.set_summary(strip_tags(overview))
            course_item["overview"] = strip_tags(overview, False)

        course_code = response.xpath("//table[@class='course-info']//td[contains(p/text(), 'Program "
                                     "No:')]/following-sibling::*/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()
        if 'courseCode' in course_item and 'uid' in course_item:
            course_item['uid'] = course_item['uid'] + '-' + course_item['courseCode']

        duration = response.xpath("//table[@class='course-info']//td[contains(p/text(), 'Duration:')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart)",
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
                                           duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        dom_fee = response.xpath("//table[@class='course-info']//td[contains(p/text(), 'Indicative "
                                 "Cost:')]/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)

        career = response.xpath("//table[@class='course-info']//td[contains(p/text(), 'Likely Job "
                                "Outcome:')]/following-sibling::*").get()
        if career:
            course_item['careerPathways'] = strip_tags(career, False)

        entry = response.xpath("//*[@id='entry']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(entry):
            if re.search('click here to apply now', item, re.I | re.M):
                pass
            elif index == 0 or re.search('^<p', item) or re.search('^<ul', item) or re.search('^<ol', item):
                holder.append(item)
            else:
                break
        if holder:
            course_item['entryRequirements'] = strip_tags(''.join(holder), False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
