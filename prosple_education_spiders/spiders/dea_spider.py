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


class DeaSpiderSpider(scrapy.Spider):
    name = 'dea_spider'
    allowed_domains = ['www.deakin.edu.au', 'deakin.edu.au']
    start_urls = [
        'https://www.deakin.edu.au/courses/find-a-course/undergraduate',
        'https://www.deakin.edu.au/courses/find-a-course/postgraduate',
        'https://www.deakin.edu.au/courses/find-a-course/research-degrees'
    ]
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = [
        '//www.deakin.edu.au/course/bachelor-criminology-bachelor-cyber-security']
    institution = 'Deakin University'
    uidPrefix = 'AU-DEA-'

    campuses = {
        "Cloud": "52597",
        "Warrnambool": "584",
        "Waurn Ponds": "582",
        "Waterfront": "581",
        "Burwood": "579"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "foundation certificate": "4",
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
        courses = response.xpath("//td/a[text()='More Info']/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
                if not re.search(r"-international", item):
                    yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//div[contains(@class, 'module__overview--course--content')]/*").getall()
        holder = []
        for item in overview:
            if not re.search('Read More', item, re.M):
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder if strip_tags(x) != ""]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath(
            "//dt[text()='CRICOS code']/following-sibling::dd/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ', '.join(cricos)
                course_item['internationalApps'] = 1
                course_item['internationalApplyURL'] = response.request.url

        course_code = response.xpath(
            "//dt[text()='Deakin code']/following-sibling::dd/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()
            course_item['uid'] = course_item['uid'] + \
                '-' + course_item['courseCode']

        course_structure = response.xpath("//div[contains(@class, 'module__content-panel--title') and */text()='Course "
                                          "structure']/following-sibling::*[contains(@class, "
                                          "'module__content-panel--text')]/*").getall()
        holder = []
        for item in course_structure:
            if not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item['courseStructure'] = strip_tags(''.join(holder), remove_all_tags=False,
                                                        remove_hyperlinks=True)

        entry = response.xpath("//div[@class='module__content-panel--title'][*[text()='Entry "
                               "information']]/following-sibling::*[contains(@class, "
                               "'module__content-panel--text')]/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(' '.join(entry), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        credit = response.xpath("//div[contains(@class, 'module__content-panel--title') and */text()='Recognition of prior "
                                "learning']/following-sibling::*[contains(@class, "
                                "'module__content-panel--text')]/*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(
                ''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//div[contains(@class, 'module__content-panel--title') and */text()='Career "
                                "outcomes']/following-sibling::*[contains(@class, "
                                "'module__content-panel--text')]/*").getall()
        if career:
            course_item['careerPathways'] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath(
            "//div[contains(h3/text(), 'Campuses') and @class='module__summary--icon-wrapper']/following-sibling::div").getall()
        if location:
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)
            study_holder = set()
            if len(campus_holder) == 1:
                if re.search("online", location, re.I | re.M):
                    study_holder.add("Online")
                else:
                    study_holder.add("In Person")
            if len(campus_holder) > 1:
                if re.search("online", location, re.I | re.M):
                    study_holder.add("Online")
                study_holder.add("In Person")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        atar = response.xpath(
            "//div[contains(h3/text(), 'ATAR') and @class='module__summary--icon-wrapper']/following-sibling::div").getall()
        if atar:
            atar = re.findall("\d{1,2}\.\d{1,2}", atar)
            if atar:
                atar = [float(x) for x in atar]
                course_item["guaranteedEntryScore"] = max(atar)

        duration = response.xpath(
            "//div[contains(h3/text(), 'Duration') and @class='module__summary--icon-wrapper']/following-sibling::div").getall()
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
                    course_item["durationMinFull"] = min(
                        float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(
                        float(duration_full[0][0]), float(duration_full[0][1]))
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

        intake = response.xpath(
            "//div[contains(@class, 'module__content-panel--title') and */text()='Campuses by intake']/following-sibling::*[contains(@class, 'module__content-panel--text')]//*[@class='module__accordion--title']").getall()
        if intake:
            intake = "".join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
