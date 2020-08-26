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


class RmiSpiderSpider(scrapy.Spider):
    name = 'rmi_spider'
    start_urls = ['https://www.rmit.edu.au/study-with-us']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "RMIT University"
    uidPrefix = "AU-RMI-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "phd": "6",
        "certificate": "4",
        "victorian certificate": "4",
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
        "Point Cook": "11706",
        "Bundoora": "690",
        "Melbourne City": "689",
        "Brunswick": "691"
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
        yield SplashRequest(response.request.url, callback=self.category_parse, args={'wait': 20})

    def category_parse(self, response):
        categories = response.xpath("//div[@class='target_EF']//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[contains(@class, 'columnlinklist__content--box')]//a["
                             "@data-analytics-type='columnlinklist']/@href").getall()

        for item in sub:
            yield SplashRequest(response.urljoin(item), callback=self.link_parse, args={'wait': 20})

    def link_parse(self, response):
        courses = response.xpath("//a[@data-analytics-type='program list']/@href").getall()

        for item in courses:
            yield response.follow(response.urljoin(item), callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_name = re.sub('\s-.*', '', course_name)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                  "'Overview')]/following-sibling::div[not(@class='module')][1]/div[contains(@class, "
                                  "'extended-desc')]/*").getall()
        if not overview or strip_tags(''.join(overview)).strip() == '':
            overview = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                      "'Details')]/following-sibling::div[not(@class='module')][1]/div[contains("
                                      "@class, 'extended-desc')]/p").getall()
        if overview:
            course_item['overview'] = strip_tags(''.join(overview), False)

        summary = response.xpath("//*[@class='program-tilte']/text()").get()
        if summary:
            course_item.set_summary(strip_tags(summary.strip()))

        career = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                "'Career')]/following-sibling::div[1]/div[contains(@class, "
                                "'extended-desc')]/*").getall()
        if not career or strip_tags(''.join(career)).strip() == '':
            career = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                                    "'Career')]/following-sibling::div[1]/div[contains(@class, "
                                    "'extended-desc')]/text()").getall()
            career = [x for x in career if strip_tags(x).strip() != '']
        if career:
            course_item['careerPathways'] = strip_tags(''.join(career), False)

        location = response.xpath("//*[@class='description'][text()='Location']/following-sibling::*").getall()
        campus_holder = set()
        study_holder = set()
        if location:
            location = '|'.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if re.search('online', location, re.I | re.M):
                study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        duration = response.xpath("//*[contains(@class, 'b-domestic')]//*[@class='description'][text("
                                  ")='Duration']/following-sibling::*").get()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall("(?<=full.time\s)(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(?<=part.time\s)(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
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
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        intake = response.xpath("//*[@class='description'][text()='Next intake']/following-sibling::*").getall()
        if intake:
            intake = ''.join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        dom_fee = response.xpath("//*[contains(@class, 'b-domestic')]//h4[@class='description'][text("
                                 ")='Fees']/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)", dom_fee, re.M)
            if dom_fee:
                course_item["domesticFeeAnnual"] = float(''.join(dom_fee[0]))
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//*[contains(@class, 'b-international')]//h4[@class='description'][text("
                                 ")='Fees']/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)", int_fee, re.M)
            if int_fee:
                course_item["internationalFeeAnnual"] = float(''.join(int_fee[0]))
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        atar = response.xpath("//*[@class='description'][text()='Entry score']/following-sibling::*").get()
        if atar:
            atar = re.findall("(?<=ATAR\s)(\d*),?(\d+)", atar, re.M)
            if atar:
                course_item["guaranteedEntryScore"] = float(''.join(atar[0]))

        cricos = response.xpath("//table[contains(@class, 'program-table')]//td[last()-1]/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = cricos[0]
                course_item["internationalApps"] = 1

        course_code = response.xpath("//table[contains(@class, 'program-table')]//td[last()-2]/text()").get()
        if course_code:
            course_item['courseCode'] = course_code

        entry = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                               "'Admissions')]/following-sibling::div[1]/div[contains(@class, "
                               "'extended-desc')]/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), False)

        credit = response.xpath(
            "//*[contains(text(), 'Credit and recognition of prior learning')]/following-sibling::*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(''.join(credit), False)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        if 'uid' in course_item and 'courseCode' in course_item:
            course_item['uid'] = course_item['uid'] + '-' + course_item['courseCode']

        yield course_item

