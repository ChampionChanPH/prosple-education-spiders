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


class SeroSpiderSpider(scrapy.Spider):
    name = 'sero_spider'
    start_urls = ['https://seroinstitute.com.au/']
    institution = "SERO Institute"
    uidPrefix = "AU-SERO-"

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
        "Perth Campus": "83033",
        "Gold Coast Campus": "83032",
        "Brisbane Campus": "83031"
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
        sub = response.xpath("//a[@class='menu-link' and text()='Courses']/following-sibling::ul["
                             "@class='sub-menu']//ul[@class='sub-menu']//a")
        yield from response.follow_all(sub, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//a[span/span/text()='Course Info']/@href").getall()

        for item in courses:
            if not re.search("seroinstitute.com.au/contact/", item):
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.xpath("//*[self::h1 or self::h2][contains(@class, 'elementor-heading-title')]/text()").get()
        if name:
            if re.search("[A-Z]+[0-9]+ ", name):
                course_code, course_name = re.split("\\s", name, maxsplit=1)
                course_name = course_name.replace("\n", " ")
                course_item.set_course_name(course_name.strip(), self.uidPrefix)
                course_item["courseCode"] = course_code
            else:
                course_item.set_course_name(name.strip(), self.uidPrefix)
        if "courseCode" not in course_item:
            course_code = response.xpath("//h6[contains(@class, 'elementor-heading-title')]/text()").get()
            if course_code and re.search("[A-Z]+[0-9]+", course_code):
                course_item["courseCode"] = course_code

        overview = response.xpath(
            "//*[@data-element_type='widget' and */h1[contains(@class, 'elementor-heading-title')]]"
            "/following-sibling::*//*[self::p or self::ol or self::ul]").getall()
        if not overview:
            overview = response.xpath(
                "//*[@data-element_type='widget' and */*/text()='Course overview']"
                "/following-sibling::*//*[self::p or self::ol or self::ul]").getall()
        if not overview:
            xpath_value = "//*[@data-element_type='widget' and */*/text()='" + name.strip() + \
                          "']/following-sibling::*[1]//*[self::p or self::ol or self::ul]"
            overview = response.xpath(xpath_value).getall()
        if not overview:
            overview = response.xpath(
                "//*[@data-element_type='widget' and */h3[contains(@class, 'elementor-heading-title')] and "
                "*/*/text()='Reason for studying & Skills learned: ']"
                "/following-sibling::*//*[self::p or self::ol or self::ul]").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//*[@data-element_type='widget' and */h2/text()='Entry Requirements']"
            "/following-sibling::*//*[self::p or self::ol or self::ul]").getall()
        if not entry:
            entry = response.xpath(
                "//*[contains(@id, 'elementor-tab-title') and */text()='Entry Requirements']"
                "/following-sibling::*/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//*[contains(@id, 'elementor-tab-title') and */text()='Career Opportunities']"
            "/following-sibling::*/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        study = response.xpath(
            "//*[@data-element_type='widget' and */*/text()='Delivery methods']"
            "/following-sibling::*//*[self::p or self::ol or self::ul]").getall()
        study_holder = set()
        if study:
            if re.search('online', ''.join(study), re.I):
                study_holder.add("Online")
            study_holder.add("In Person")

        duration = response.xpath(
            "//*[@data-element_type='widget' and (contains(*/h2/text(), 'Course duration') or "
            "contains(*/h2/text(), 'Course Duration'))]/following-sibling::*//*[self::p or self::ol or "
            "self::ul]").getall()
        if duration:
            duration = "".join(duration)
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
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
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
            if not study:
                if re.search('online', duration, re.I):
                    study_holder.add("Online")
                study_holder.add("In Person")

        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        course_item["campusNID"] = "83031|83032|83033"

        cricos = response.xpath("//*[contains(text(), 'CRICOS Code')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1

        yield course_item
