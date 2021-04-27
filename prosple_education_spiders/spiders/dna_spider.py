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


class DnaSpiderSpider(scrapy.Spider):
    name = 'dna_spider'
    start_urls = ['http://www.dnakingstontraining.edu.au/courses/']
    banned_urls = ['http://www.dnakingstontraining.edu.au/#']
    institution = "DNA Kingston Training"
    uidPrefix = "AU-DNA-"

    degrees = {
        "graduate certificate": "7",
        "executive graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "undergraduate certificate": "4",
        "university certificate": "4",
        "certificate": "4",
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
        categories = response.xpath("//div[@class='wf-container-main']//a")
        yield from response.follow_all(categories, callback=self.sub_parse)

    def sub_parse(self, response):
        categories = response.xpath("//div[@class='wf-container-main']//a/@href").getall()

        for item in categories:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            if re.search('^[A-Z]+[0-9]+', course_name):
                course_name = re.sub('^[A-Z]+[0-9]+', '', course_name)
                course_code = re.findall('^[A-Z]+[0-9]+', course_name)
                if course_code:
                    course_item['courseCode'] = ', '.join(course_code)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@id='main']//div[contains(@class, 'vc_row-fluid')][1]//div[contains(@class, "
                                  "'wpb_content_element')]/div[@class='wpb_wrapper'][1]/*[self::* or self::text("
                                  ")]").getall()
        if overview:
            overview = [x for x in overview if strip_tags(x) != '']
            overview = [x for x in overview if not re.search('<img', x)]
            if overview:
                summary = [strip_tags(x) for x in overview]
                course_item.set_summary(' '.join(summary))
                course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        menu = response.xpath("//nav//span/text()").getall()

        if 'Entry requirements' in menu:
            index = menu.index('Entry requirements')
            entry_xpath = "//div[@class='et-content-wrap']/section[" + str(index) + "]//div[@class='wpb_wrapper']/*"
            entry = response.xpath(entry_xpath).getall()
            if entry:
                entry = [x for x in entry if strip_tags(x) != '']
                if entry:
                    course_item['entryRequirements'] = strip_tags(''.join(entry), remove_all_tags=False,
                                                                  remove_hyperlinks=True)

        if 'Career' in menu:
            index = menu.index('Career')
            career_xpath = "//div[@class='et-content-wrap']/section[" + str(index) + "]//div[@class='wpb_wrapper']/*"
            career = response.xpath(career_xpath).getall()
            if career:
                career = [x for x in career if strip_tags(x) != '']
                if career:
                    course_item['careerPathways'] = strip_tags(''.join(career), remove_all_tags=False,
                                                               remove_hyperlinks=True)

        if 'International students' in menu:
            index = menu.index('International students')
            int_xpath = "//div[@class='et-content-wrap']/section[" + str(index) + "]//div[@class='wpb_wrapper']/*"
            international = response.xpath(int_xpath).getall()
            if international:
                international = ''.join(international)

                duration = re.sub(' \([0-9]+\)', '', international)
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

                int_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", international, re.M)
                int_fee = [float(''.join(x)) for x in int_fee]
                if int_fee:
                    course_item["internationalFeeAnnual"] = max(int_fee)
                    get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        cricos = response.xpath("//*[contains(text(), 'CRICOS')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        yield course_item
