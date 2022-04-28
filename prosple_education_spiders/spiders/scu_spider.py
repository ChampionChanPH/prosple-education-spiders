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


class ScuSpiderSpider(scrapy.Spider):
    name = 'scu_spider'
    start_urls = ['https://course-search.scu.edu.au/']
    institution = "Southern Cross University (SCU)"
    uidPrefix = "AU-SCU-"

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
        "vcal in victorian certificate": "9",
        "vcal in": "9",
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
        "Melbourne": "701",
        "Lismore": "695",
        "Gold Coast": "696",
        "Perth": "700",
        "Sydney": "699",
        "Tweed Heads": "698",
        "Coffs Harbour": "697",
        "National Marine Science Centre": "694",
    }

    key_dates = {
        "1": "03",
        "2": "07",
        "3": "11"
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
        courses = response.xpath("//div[@class='row results']//a[contains(@class, 'text-primary')]/@href").getall()

        for item in courses:
            item = re.sub('202[2-3]/$', '', item.strip())
            yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//a[@class='page-link'][contains(*/@class, 'angle-right')]/@href").get()

        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='pageTitleFixSource']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath(
            "//h1[@class='pageTitleFixSource']/following-sibling::*[contains(text(), 'Course Code')]").get()
        if course_code:
            course_code = re.findall("(?<=Course Code: )\w+", course_code, re.I)
            if course_code:
                course_item["courseCode"] = course_code[0]
                if 'uid' in course_item:
                    course_item['uid'] = course_item['uid'] + '-' + course_item['courseCode']

        overview = response.xpath("//*[text()='Course summary']/following-sibling::*/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False)

        duration = response.xpath("//div[@id='domestic']//td[text()='Duration']/following-sibling::*").get()
        if not duration:
            duration = response.xpath("//div[@id='international']//td[text()='Duration']/following-sibling::*").get()
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
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        location = response.xpath("//td[text()='Availability details']/following-sibling::*").getall()
        campus_holder = set()
        study_holder = set()
        online_course_only = False
        if location:
            location = [strip_tags(x) for x in location if strip_tags(x) != '']
            location = '|'.join(location)
            if re.search('SCU Online', location, re.I):
                online_course_only = True
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if re.search('online', location, re.I):
                study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        dom_fee = response.xpath(
            "//div[@id='domestic']//td[text()='Availability details']/following-sibling::*").getall()
        if dom_fee:
            dom_fee = ''.join(dom_fee)
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath(
            "//div[@id='international']//td[text()='Availability details']/following-sibling::*").getall()
        if int_fee:
            int_fee = ''.join(int_fee)
            int_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        cricos = response.xpath(
            "//div[@id='international']//td[text()='Availability details']/following-sibling::*").getall()
        if cricos:
            cricos = ''.join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        atar = response.xpath("//td[contains(text(), 'ATAR')]/following-sibling::*/text()").get()
        if atar:
            atar = re.findall('\d+?(?= /)', atar, re.M)
            if atar:
                course_item['guaranteedEntryScore'] = float(atar[0])

        career = response.xpath("//div[@id='collapseCrsCO']/div[@class='card-body']/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(''.join(career), remove_all_tags=False)

        learn = response.xpath("//div[@id='collapseCrsMAS']/div[@class='card-body']/*").getall()
        if learn:
            course_item["whatLearn"] = strip_tags(''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//*[text()='Course requirements']/following-sibling::div[@class='req-list'][1]/*").getall()
        if structure:
            course_item["courseStructure"] = strip_tags(''.join(structure), remove_all_tags=False)

        entry = response.xpath(
            "//*[text()='Admission requirements']/following-sibling::div[@class='req-list'][1]/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        if 'courseName' in course_item and not online_course_only:
            course_item.set_sf_dt(self.degrees, degree_delims=["and", "/", ","], type_delims=["of", "in", "by"])

            yield course_item
