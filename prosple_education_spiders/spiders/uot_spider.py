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


class UotSpiderSpider(scrapy.Spider):
    name = 'uot_spider'
    start_urls = ['https://www.utas.edu.au/courses/undergraduate',
                  'https://www.utas.edu.au/courses/postgraduate']
    institution = "University of Tasmania"
    uidPrefix = "AU-UOT-"

    campuses = {
        "Rozelle": "815",
        "Launceston": "810",
        "Distance Launceston": "813",
        "Darlinghurst": "816",
        "Distance Sydney": "817",
        "Distance Hobart": "814",
        "Hobart": "811",
        "Cradle Coast": "812"
    }

    terms = {"Term 1": "02",
             "Term 2": "04",
             "Term 3": "07",
             "Term 4": "10",
             "Semester 1": "02",
             "Semester 2": "07"}

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
        "victorian certificate": "9",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//div[@id='courseList']//div[@class='content-border']//a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='l-object-page-header--page-title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//h1[@class='l-object-page-header--page-title']/small/text()").get()
        course_code = re.findall("(?<=\().+?(?=\))", course_code, re.DOTALL)
        if course_code:
            course_item["courseCode"] = ', '.join(course_code)

        summary = response.xpath("//div[@class='richtext richtext__medium']/div[@class='lede']/text()").get()
        overview = response.xpath(
            "//div[@class='block block__gutter-md block__shadowed']/div[@class='block block__pad-lg']/div["
            "@class='richtext richtext__medium']/*[not(contains(@class, 'lede'))]").getall()
        if overview:
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)
            summary_holder = []
            if summary:
                summary_holder.append(summary)
            summary_holder.append([strip_tags(x) for x in overview])
            course_item.set_summary(' '.join(summary))

        duration = response.xpath("//dt[contains(*[@class='t-shark']/text(), 'Duration')]/following-sibling::dd").get()
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

        location = response.xpath("//*[@class='t-shark'][contains(text(), 'Location')]/following-sibling::dl").get()
        campus_holder = set()
        intake_holder = []
        if location:
            for campus in self.campuses:
                if campus in ["Launceston", "Hobart"]:
                    if re.search('(?<!Distance\s)' + campus, location, re.M | re.I):
                        campus_holder.add(self.campuses[campus])
                else:
                    if re.search(campus, location, re.M | re.I):
                        campus_holder.add(self.campuses[campus])
            for term in self.terms:
                if re.search(term, location, re.M | re.I):
                    intake_holder.append(self.terms[term])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
        if intake_holder:
            course_item['startMonths'] = '|'.join(intake_holder)

        study_holder = set()
        if "campusNID" in course_item:
            if re.search("813|814|817", course_item["campusNID"]) and re.search("810|811|812|815|816",
                                                                                course_item["campusNID"]):
                study_holder.add('In Person')
                study_holder.add('Online')
            elif re.search("810|811|812|815|816", course_item["campusNID"]):
                study_holder.add('In Person')
            elif re.search("813|814|817", course_item["campusNID"]):
                study_holder.add('Online')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        cricos = response.xpath("//abbr[text()='CRICOS']/following-sibling::text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(set(cricos))
                course_item["internationalApps"] = 1

        # course_item["domesticApplyURL"] = response.request.url
        # course_item["internationalApplyURL"] = response.request.url

        entry = response.xpath("//div[@id='c-entry-eligibility']/*/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath("//div[@id='c-entry-credittransfer']/*/*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//*[@id='career-outcomes']/following-sibling::*[1]//*[contains(@class, "
                                "'richtext__medium')]/*").getall()
        if career:
            course_item['careerPathways'] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath("//*[@id='course-structure']/following-sibling::*[1]//*[contains(@class, "
                                   "'richtext__medium')]/*").getall()
        holder = []
        for index, item in enumerate(structure):
            if not re.search('^<(p|o|u)', item) and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            course_item['courseStructure'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        int_fee = response.xpath("//*[@class='sectioned-content--title'][contains(text(), 'International "
                                 "students')]/following-sibling::*[1]//*[contains(@class, "
                                 "'richtext__medium')]/*").get()
        if int_fee:
            total_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?(?=\sAUD\*)", int_fee, re.M)
            total_fee = [float(''.join(x)) for x in total_fee]
            if total_fee:
                course_item["internationalFeeTotal"] = max(total_fee)

            annual_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?(?=\sAUD per standard)", int_fee, re.M)
            annual_fee = [float(''.join(x)) for x in annual_fee]
            if annual_fee:
                course_item["internationalFeeAnnual"] = max(annual_fee)

        yield course_item
