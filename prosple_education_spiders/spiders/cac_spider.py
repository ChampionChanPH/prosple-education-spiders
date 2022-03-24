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
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])


class CacSpiderSpider(scrapy.Spider):
    name = 'cac_spider'
    start_urls = ['https://www.canningcollege.wa.edu.au/programs/']
    institution = "Canning College"
    uidPrefix = "AU-CAC-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "western australian certificate": "9",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "year 10": "9",
        "year 11": "9",
        "year 12 - western australian certificate": "9",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//a[@class='raven-post-button']")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath(
            "//h1[contains(@class, 'elementor-heading-title')]/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//h1/ancestor::section/following-sibling::*[1]//div[contains(@class, elementor-text-editor)]/*[self::h2 or self::h3]/following-sibling::*").getall()
        holder = []
        for item in overview:
            if strip_tags(item) == "":
                break
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder if strip_tags(x) != '']
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        intake = response.xpath(
            "//*[text()='INTAKE & DURATION']/following-sibling::*").getall()
        holder = []
        if intake:
            intake = "".join(intake)
            for item in self.months:
                if re.search(item, intake):
                    holder.append(self.months[item])
        if holder:
            course_item["startMonths"] = "|".join(holder)

        # duration = response.xpath(
        #     "//div[contains(@class, 'bodyContent_Course_Duration')]").getall()
        # if duration:
        #     duration = "".join(duration)
        #     duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
        #                                duration, re.I | re.M | re.DOTALL)
        #     if duration_full:
        #         course_item["durationMinFull"] = float(duration_full[0][0])
        #         self.get_period(duration_full[0][1].lower(), course_item)

        entry = response.xpath(
            "//*[text()='PREREQUISITES']/following-sibling::*").getall()
        if entry:
            entry = [strip_tags(x) for x in entry if strip_tags(x) != '']
            course_item['entryRequirements'] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        dom_fee = response.xpath(
            "//*[text()='COST']/following-sibling::*").getall()
        if dom_fee:
            dom_fee = ''.join(dom_fee)
            dom_fee = re.findall(
                "\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
                course_item["internationalFeeTotal"] = max(dom_fee)

        apply = response.xpath(
            "//div[contains(@class, 'bodyContent_Enrolment_Details')]/*").getall()
        if apply:
            course_item['howToApply'] = strip_tags(
                ''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//*[text()='TUITION']/following-sibling::*").getall()
        if structure:
            structure = [strip_tags(x)
                         for x in structure if strip_tags(x) != '']
            course_item['courseStructure'] = strip_tags(''.join(structure), remove_all_tags=False,
                                                        remove_hyperlinks=True)

        cricos = response.xpath(
            "//*[contains(text(), 'CRICOS Course Code')]").get()
        if not cricos:
            cricos = response.xpath(
                "//*[contains(text(), 'Course Code')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_item["campusNID"] = "30901"

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        if course_item['courseName'] == 'Preparation for Year 10 and Year 11':
            course_item['rawStudyfield'] = [course_item['courseName'].lower()]
            course_item['degreeType'] = 'Non-Award'
            course_item['doubleDegree'] = None
            course_item['specificStudyField'] = course_item['courseName']

        yield course_item
