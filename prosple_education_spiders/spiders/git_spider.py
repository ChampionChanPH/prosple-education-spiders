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


class GitSpiderSpider(scrapy.Spider):
    name = 'git_spider'
    start_urls = ['https://www.thegordon.edu.au/courses/international']

    international_courses = []

    institution = "The Gordon"
    uidPrefix = "AU-GIT-"

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
        "vcal - victorian certificate": "9",
        "vce - victorian certificate": "9",
        "non-award": "13",
        "no match": "15"
    }

    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    campuses = {
        "Geelong City Campus": "58312",
        "East Geelong Campus": "58313",
        "Werribee": "58314",
        "Hoppers Crossing Trades Campus": "58314",
        "Colac Trade Training Centre": "58315",
        "Workplace": "58316",
        "Off Campus": "58316",
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
        courses = response.xpath("//*[@id='pageCourseSearchDiv']//*[@class='ResultRow']//a/text()").getall()
        courses = [x.strip() for x in courses]
        self.international_courses.extend(courses)

        check_page = response.xpath("//*[@class='Pages']").get()
        if check_page:
            check_page = re.findall('(\d+) of (\d+)', check_page)
            if check_page:
                if check_page[0][0] != check_page[0][1]:
                    next_page = response.xpath("//a[text()='>']/@href").get()
                    if next_page:
                        yield response.follow(next_page, callback=self.parse)
                else:
                    all_course = 'https://www.thegordon.edu.au/courses/all-courses'
                    yield response.follow(all_course, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//*[@id='pageCourseSearchDiv']//*[@class='ResultRow']//a")
        yield from response.follow_all(courses, callback=self.course_parse)

        check_page = response.xpath("//*[@class='Pages']").get()
        if check_page:
            check_page = re.findall('(\d+) of (\d+)', check_page)
            if check_page and check_page[0][0] != check_page[0][1]:
                next_page = response.xpath("//a[text()='>']/@href").get()
                if next_page:
                    yield response.follow(next_page, callback=self.sub_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        name_with_code = response.xpath("//h1/text()").get()
        if name_with_code:
            course_code = re.findall('^[0-9A-Z]+', name_with_code)
            if course_code:
                course_item['courseCode'] = course_code[0]
            course_name = re.findall('[0-9A-Z]+?\s(.*)', name_with_code, re.DOTALL)
            if course_name:
                course_name = re.sub('~', '', course_name[0])
                course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[text()='Course description']/following-sibling::node()").getall()
        holder = []
        for index, item in enumerate(overview):
            if re.search('^<(h|a|d)', item):
                if index == 0:
                    pass
                else:
                    break
            else:
                holder.append(item)
        if holder:
            holder = [x for x in holder if strip_tags(x) != '']
            if holder:
                summary = [strip_tags(x) for x in holder]
                course_item.set_summary(' '.join(summary))
                course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
        if 'overview' not in course_item:
            for index, item in enumerate(overview):
                if re.search('^<(h|a|d)', item):
                    if index == 0 and index == 1:
                        pass
                    else:
                        break
                else:
                    holder.append(item)
            if holder:
                holder = [x for x in holder if strip_tags(x) != '']
                if holder:
                    summary = [strip_tags(x) for x in holder]
                    course_item.set_summary(' '.join(summary))
                    course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//*[text()='Possible career outcomes']/following-sibling::node()").getall()
        holder = []
        for index, item in enumerate(career):
            if re.search('^<(h|a|d)', item):
                if index == 0:
                    pass
                else:
                    break
            else:
                holder.append(item)
        if holder:
            holder = [x for x in holder if strip_tags(x) != '']
            if holder:
                course_item["careerPathways"] = strip_tags(''.join(holder), remove_all_tags=False,
                                                           remove_hyperlinks=True)

        intake = response.xpath("//div[@id='IntakesTable']").get()
        if intake:
            holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

            duration = re.sub('yr', 'year', intake)
            duration_full = re.findall("(?<=full.time.\s)(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M |
                                       re.DOTALL)
            duration_part = re.findall("(?<=part.time.\s)(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M |
                                       re.DOTALL)
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

        location = response.xpath("//div[@id='IntakesTable']").get()
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        entry = response.xpath("//*[contains(@class, 'accordionHeader')][contains(text(), 'Entrance "
                               "Requirements')]/following-sibling::*/*/*/*[@style='display: block;']/*[text("
                               ")='Entrance Requirements / Pre-requisites']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(entry):
            if re.search('display: none', item):
                if index == 0:
                    pass
                else:
                    break
            else:
                holder.append(item)
        if holder:
            holder = [x for x in holder if strip_tags(x) != '']
            if holder:
                course_item["entryRequirements"] = strip_tags(''.join(holder), remove_all_tags=False,
                                                              remove_hyperlinks=True)

        dom_fee = response.xpath("//div[@id='FeeTable']/div[@class='row']/*[contains(text(), 'Full Fee "
                                 "Tuition')]/following-sibling::*[last()-1]").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//div[@id='FeeTable']/div[@class='row']/*[contains(text(), 'Standard "
                                 "Tuition')]/following-sibling::*[last()-1]").get()
        if csp_fee:
            csp_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            csp_fee = [float(''.join(x)) for x in csp_fee]
            if csp_fee:
                course_item["domesticSubFeeTotal"] = max(csp_fee)
                # get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        if 'courseName' in course_item:
            if re.search('\smaster\s', course_item['courseName'], re.I):
                course_item['courseLevel'] = 'Undergraduate'
                course_item['degreeType'] = 'Non-Award'

        if course_item['courseName'] in self.international_courses:
            yield response.follow(response.request.url + '?i=1', callback=self.int_parse, meta={'item': course_item})
        else:
            yield course_item

    def int_parse(self, response):
        course_item = response.meta['item']

        cricos = response.xpath("//*[contains(text(), 'CRICOS code:')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(set(cricos))

        int_fee = response.xpath("//*[contains(text(), 'Total tuition fee:')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        course_item["internationalApps"] = 1

        yield course_item
