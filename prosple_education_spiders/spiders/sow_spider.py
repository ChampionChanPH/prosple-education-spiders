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


class SowSpiderSpider(scrapy.Spider):
    name = 'sow_spider'
    start_urls = ['https://www.swtafe.edu.au/courses/free-tafe-courses']
    institution = "South West TAFE"
    uidPrefix = "AU-SOW-"

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
        "Heidelberg": "57293",
        "Epping": "57292",
        "Fairfield": "57291",
        "Preston": "57290",
        "Greensborough": "57294",
        "Prahran": "57295",
        "Collingwood": "57296",
        "Eden Park at Northern Lodge": "57297",
        "Yan Yean at Northern Lodge": "57299",
        "Online": "57300",
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
            "//h3[contains(@class, 'content-heading-secondary')]/following-sibling::*[1]//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='intro__title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//td[text()='Course Code']/following-sibling::*/text()").get()
        if course_code:
            course_item['courseCode'] = course_code

        overview = response.xpath(
            "//div[contains(@class, 'content-heading-secondary')][text()='Introduction']/following-sibling::*").getall()
        holder = []
        if overview:
            overview = [x for x in overview if strip_tags(x) != '']
            for item in overview:
                if not re.search('^<(p|o|u)', item):
                    break
                else:
                    holder.append(item)
        if holder:
            course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
            course_item.set_summary(strip_tags(''.join(holder)))

        learn = response.xpath(
            "//div[contains(@class, 'content-heading-secondary')][text()='What will I Learn?']/following-sibling::*").getall()
        holder = []
        if learn:
            learn = [x for x in learn if strip_tags(x) != '']
            for item in learn:
                if not re.search('^<(p|o|u)', item):
                    break
                else:
                    holder.append(item)
        if holder:
            course_item["whatLearn"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//div[contains(@class, 'content-heading-secondary')][text()='Course Outcomes and "
                                "Career Opportunities']/following-sibling::*").getall()
        holder = []
        if career:
            career = [x for x in career if strip_tags(x) != '']
            for item in career:
                if not re.search('^<(p|o|u)', item):
                    break
                else:
                    holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//div[contains(@class, 'content-heading-secondary')][text()='Entrance requirements & "
                               "pre-requisites']/following-sibling::*").getall()
        holder = []
        if entry:
            entry = [x for x in entry if strip_tags(x) != '']
            for item in entry:
                if not re.search('^<(p|o|u)', item):
                    break
                else:
                    holder.append(item)
        if holder:
            course_item["entryRequirements"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath("//div[contains(@class, 'content-heading-secondary')][text()='How to "
                               "apply']/following-sibling::*").getall()
        holder = []
        if apply:
            apply = [x for x in apply if strip_tags(x) != '']
            for item in apply:
                if not re.search('^<(p|o|u)', item):
                    break
                else:
                    holder.append(item)
        if holder:
            course_item["howToApply"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath("//td[text()='Locations']/following-sibling::*/text()").get()
        if location:
            course_item['campusNID'] = location.strip()

        study = response.xpath("//td[text()='Study Mode']/following-sibling::*/text()").get()
        if study:
            course_item['modeOfStudy'] = study.strip()

        intake = response.xpath("//td[text()='Commencement']/following-sibling::*/text()").get()
        if intake:
            course_item['startMonths'] = intake.strip()

        duration = response.xpath("//td[text()='Length']/following-sibling::*/text()").get()
        if duration:
            course_item['teachingPeriod'] = duration.strip()

        dom_fee = response.xpath("//td[contains(text(), 'Full fee rate')]/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = dom_fee
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//td[contains(text(), 'Government subsidised rate')]/following-sibling::*").get()
        if csp_fee:
            csp_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            csp_fee = [float(''.join(x)) for x in csp_fee]
            if csp_fee:
                course_item["domesticSubFeeAnnual"] = csp_fee
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
