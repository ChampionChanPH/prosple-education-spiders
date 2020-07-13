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
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


class WaifsSpiderSpider(scrapy.Spider):
    name = 'waifs_spider'
    allowed_domains = ['waifs.wa.edu.au']
    start_urls = ['http://waifs.wa.edu.au/courses/']
    banned_urls = []
    institution = "West Australian Institute of Further Studies"
    uidPrefix = "AU-WAIFS-"

    campuses = {
        "Perth": "30939"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
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
        "December": "12",
        "Monthly": "01|02|03|04|05|06|07|08|09|10|11|12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//ul[@id='menu-main-menu-1']//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//div[@class='course-intro']/following-sibling::ul//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        code = response.xpath("//strong[@class='course__information--label'][contains(text(), 'Course "
                              "Code')]/following-sibling::*//text()").get()
        if code:
            course_item['courseCode'] = code.strip()

        course_name = response.xpath("//h1[@class='course__title']/text()").get()
        course_name = re.sub(course_item['courseCode'], '', course_name)
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//h2[contains(text(), 'Course Outline')]/following-sibling::*").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            course_item["overview"] = strip_tags("".join(overview), False)

        duration = response.xpath("//strong[@class='course__information--label'][contains(text(), "
                                  "'Duration')]/following-sibling::*//text()").get()
        if duration:
            duration = re.sub("\(.*\)", "", duration, re.DOTALL)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(?<=part.time.equivalent.up.to.)(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
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

        intake = response.xpath("//strong[@class='course__information--label'][contains(text(), 'Next Intake "
                                "Date')]/following-sibling::*//text()").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        entry = response.xpath("//a[contains(text(), 'Entry Requirements')]/following-sibling::*/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags("".join(entry), False)

        dom_fee = response.xpath("//a[contains(text(), 'Domestic Fees')]/following-sibling::*/*").getall()
        if dom_fee:
            dom_fee = "".join(dom_fee)
            dom_fee = re.findall("(?<=\$)(\d*),?\s?(\d+)", dom_fee, re.M)
            if dom_fee:
                course_item["domesticFeeAnnual"] = float(dom_fee[0][0] + dom_fee[0][1])
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//a[contains(text(), 'International Fees')]/following-sibling::*/*").getall()
        if int_fee:
            int_fee = "".join(int_fee)
            int_fee = re.findall("(?<=\$)(\d*),?\s?(\d+)", int_fee, re.M)
            if int_fee:
                course_item["internationalFeeAnnual"] = float(int_fee[0][0] + int_fee[0][1])
                if re.search("per week", int_fee, re.I | re.M) and 'durationMinFull' in course_item:
                    course_item['internationalFeeTotal'] = course_item['internationalFeeAnnual'] * course_item['durationMinFull']
                else:
                    get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        course_item['group'] = 23
        course_item['canonicalGroup'] = "StudyPerth"
        course_item['campusNID'] = "30939"

        if 'internationalFeeAnnual' in course_item:
            course_item["internationalApps"] = 1
            course_item["internationalApplyURL"] = response.request.url

        yield course_item
