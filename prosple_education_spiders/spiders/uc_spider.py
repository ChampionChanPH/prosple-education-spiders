# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by: Christian Anasco on 1st May, 2021

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


class UcSpiderSpider(scrapy.Spider):
    name = 'uc_spider'
    start_urls = ['https://www.canterbury.ac.nz/study/qualifications-and-courses/']
    blacklist_urls = [
        "https://www.canterbury.ac.nz/study/qualifications-and-courses/bachelors-degrees/double-degrees/",
        "https://www.canterbury.ac.nz/study/study-abroad-and-exchange/outgoing-exchange-current-uc-students/insurance"
        "-for-outgoing-students/",
    ]

    institution = "University of Canterbury"
    uidPrefix = "NZ-UC-"

    degrees = {
        "postgraduate certificate": "7",
        "graduate certificate": "7",
        "postgraduate diploma": "8",
        "graduate diploma": "8",
        "professional master": "11",
        "master": research_coursework,
        "masters": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "victorian certificate": "4",
        "undergraduate certificate": "4",
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
        courses = response.xpath("//ul[@id='submenu-2']/li[ul]//li/a/@href").getall()
        for item in courses:
            if item not in self.blacklist_urls:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url
        course_item["campusNID"] = "48599"

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//h3[contains(@class, 'acronym')]/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        overview = response.xpath("//div[@id='overview']/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview if strip_tags(x) != '']
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags("".join(overview), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//div[contains(@class, 'panel-heading')][*//text()='Entry "
                               "requirements']/following-sibling::*/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//div[contains(@class, 'panel-heading')][*//text()='Career "
                                "Opportunities']/following-sibling::*/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags("".join(career), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//*[text()='Duration']/following-sibling::*").get()
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

        intake = response.xpath("//*[text()='Entry times']/following-sibling::*").get()
        if intake:
            start_holder = []
            for month in self.months:
                if re.search(month + " " + str(date.today().year), intake, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        dom_fee = response.xpath("//div[@id='domfee']").get()
        if dom_fee:
            dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//div[@id='intefee']").get()
        if int_fee:
            int_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)
                course_item["internationalApplyURL"] = response.request.url

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/', ','], type_delims=['of', 'in', 'by'])

        course_item["group"] = 2
        course_item["canonicalGroup"] = "GradNewZealand"

        yield course_item