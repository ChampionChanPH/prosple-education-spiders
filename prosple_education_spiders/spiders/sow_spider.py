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
    institution = "South West Institute of TAFE"
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
        "Warrnambool": "57355",
        "Portland": "57356",
        "Hamilton": "57357",
        "Colac": "57358",
        "Sherwood Park": "57359",
        "Workplace Training": "57360",
        "Glenormiston": "57361",
    }

    numbers = {
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'nine': '9',
        'ten': '10',
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
            course_item['courseCode'] = course_code.strip()

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
        campus_holder = set()
        if location:
            for campus in self.campuses:
                if campus == 'Warrnambool':
                    if re.search('(?<!\()Warrnambool', location, re.I):
                        campus_holder.add(self.campuses[campus])
                elif re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        study = response.xpath("//td[text()='Study Mode']/following-sibling::*/text()").get()
        if study == 'Online':
            course_item['modeOfStudy'] = 'Online'
        else:
            course_item['modeOfStudy'] = 'In Person|Online'

        intake = response.xpath("//td[text()='Commencement']/following-sibling::*/text()").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)
            if re.search('any.?time', intake, re.DOTALL):
                course_item['startMonths'] = '01|02|03|04|05|06|07|08|09|10|11|12'

        duration = response.xpath("//td[text()='Length']/following-sibling::*/text()").get()
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
                for item in self.numbers:
                    duration = duration.replace(item, self.numbers[item])
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        dom_fee = response.xpath("//td[contains(text(), 'Full fee rate')]/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//td[contains(text(), 'Government subsidised rate')]/following-sibling::*").get()
        if csp_fee:
            csp_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            csp_fee = [float(''.join(x)) for x in csp_fee]
            if csp_fee:
                course_item["domesticSubFeeAnnual"] = max(csp_fee)
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
