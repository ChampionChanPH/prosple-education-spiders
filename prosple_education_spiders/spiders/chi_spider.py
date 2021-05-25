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


class ChiSpiderSpider(scrapy.Spider):
    name = 'chi_spider'
    start_urls = ['https://www.chisholm.edu.au/courses']
    banned_urls = ['https://www.chisholm.edu.au/courses/short-course/course-in-introduction-to-the-national'
                   '-disability-insurance-scheme']
    institution = "Chisholm Institute"
    uidPrefix = "AU-CHI-"
    all_upper = ['WTIA', 'EAL', 'SLR', 'STEM', 'OSHC', 'LET', 'RSA', 'SWP', 'MIG', 'ARC', 'LEP', 'AS1796', 'HSR', 'CPR',
                 'MYOB', 'OHS', 'VET']

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
        "undergraduate certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "vcal - victorian certificate": "9",
        "vce - victorian certificate": "9",
        "vce- victorian certificate": "9",
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
        "Dandenong": "58339",
        "Frankston": "58340",
        "Berwick": "58341",
        "Cranbourne": "58342",
        "Chisholm at 311": "58343",
        "Bass Coast": "58344",
        "Mornington Peninsula": "58345",
        "Workplace": "58346",
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
        categories = response.xpath("//a[contains(@id, 'rptCareerList_hypCareerLink')]")
        yield from response.follow_all(categories, callback=self.link_parse)
        # for item in categories:
        #     yield response.follow(item, callback=self.link_parse)

    def link_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'main-content-wrapper')]//ul[contains(@class, "
                                 "'primary-item-list')]//a[not(@class='shortlist')]/@href").getall()
        courses = set([re.sub('/online$', '', x) for x in courses])
        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(make_proper(course_name.strip(), self.all_upper), self.uidPrefix)

        name = response.xpath("//*[@class='stream']/text()").get()
        if name and 'courseName' in course_item:
            sub_name = re.split('[.-]', name)
            sub_name = [x for x in sub_name if strip_tags(x) != '']
            sub_name = sub_name[0].strip()
            if sub_name:
                course_item['courseName'] = course_item['courseName'] + ' - ' + make_proper(sub_name, self.all_upper)
            if re.search('VET', course_item['courseName']):
                course_item['courseName'] = re.sub('(?<=VET).*', '', course_item['courseName'], re.DOTALL | re.M)
        course_item.set_course_name(course_item['courseName'], self.uidPrefix)

        course_code = response.xpath("//dt[text()='Course code']/following-sibling::*/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        overview = response.xpath("//div[@class='paragraph-print-content']/*").getall()
        overview = [x for x in overview if strip_tags(x) != '']
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        dom_fee = response.xpath(
            "//th[contains(text(), 'Maximum full course tuition fee')]/following-sibling::*[last()]").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        location = response.xpath("//dt[text()='On campus']/following-sibling::*").get()
        campus_holder = set()
        study_holder = set()
        if location:
            location = '|'.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        online = response.xpath("//*[@class='course-tabs']//a[@title='Online']/@href").get()
        if online:
            study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        duration = response.xpath("//dt[text()='Length']/following-sibling::*/text()").get()
        if duration:
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

        intake = response.xpath("//dt[text()='Start dates']/following-sibling::*/text()").get()
        if intake:
            holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        learn = response.xpath("//div[@id='learning-outcomes']").getall()
        learn = [x for x in learn if strip_tags(x) != '']
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), False)

        career = response.xpath(
            "//*[@id='career-pathways']//*[text()='Possible job outcome']/following-sibling::*//li").getall()
        if career:
            course_item['careerPathways'] = strip_tags('<ul>' + ''.join(career) + '/<ul>', False)

        entry = response.xpath("//*[@id='prerequisites']").getall()
        entry = [x for x in entry if strip_tags(x) != '']
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), False)

        apply = response.xpath("//*[@id='how-to-apply']/*").getall()
        apply = [x for x in apply if strip_tags(x) != '']
        if apply:
            course_item['howToApply'] = strip_tags(''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        international_link = response.xpath(
            "//*[@class='course-tabs']//a[@title='International students']/@href").get()
        if international_link:
            yield response.follow(international_link, callback=self.int_parse, meta={'item': course_item})
        else:
            yield course_item

    def int_parse(self, response):
        course_item = response.meta['item']

        cricos = response.xpath("//dt[text()='CRICOS']/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(set(cricos))

        int_fee = response.xpath("//*[@id='fees-navigation']/*[@id='fees']").get()
        if int_fee:
            int_fee = re.findall("\$(\d*)[,\s]?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeTotal"] = max(int_fee)
                # get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        course_item["internationalApps"] = 1

        yield course_item
