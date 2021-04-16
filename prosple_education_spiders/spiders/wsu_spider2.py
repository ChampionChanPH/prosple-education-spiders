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


class WsuSpider2Spider(scrapy.Spider):
    name = 'wsu_spider2'
    start_urls = ['https://www.westernsydney.edu.au/future/study/courses.html']
    institution = "Western Sydney University"
    uidPrefix = "AU-WSU-"

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
        "Bankstown": "855",
        "Campbelltown": "857",
        "Hawkesbury": "11718",
        "Lithgow": "39903",
        "Liverpool City": "858",
        "Nirimba": "859",
        "Parramatta City": "860",
        "Parramatta South": "853",
        "Penrith": "856",
        "Sydney City": "854",
        "Sydney Olympic Park": "39902"
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
        categories = response.xpath("//div[contains(@class, 'component--tile')]//article[contains(@class, "
                                    "'tile__theme tile__2x2')]/a")
        yield from response.follow_all(categories, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'component--tile')]//article[contains(@class, "
                                 "'tile__1x1')]/a/@href").getall()

        for item in set(courses):
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
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[contains(@class, 'section')][2]//div[@class='tile-carousel-side']/*/*").get()
        if overview:
            course_item.set_summary(strip_tags(overview))
            course_item['overview'] = strip_tags(overview, remove_all_tags=False, remove_hyperlinks=True)

        code = response.xpath("//dt[text()='COURSE CODE']/following-sibling::*").get()
        if code:
            code = re.findall("\d+", code, re.M)
            if code:
                course_item['courseCode'] = ", ".join(code)

        cricos = response.xpath("//dt[text()='CRICOS CODE']/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        intake = response.xpath(
            "//div[contains(@class, 'head')][div/text()='Start times']/following-sibling::*").getall()
        holder = []
        if intake:
            intake = '|'.join(intake)
            for month in self.months:
                if re.search(month, intake, re.M):
                    holder.append(self.months[month])
        if holder:
            course_item["startMonths"] = "|".join(holder)

        full_time = response.xpath("//div[contains(@class, 'label')][text()='FULL TIME']/following-sibling::*").get()
        part_time = response.xpath("//div[contains(@class, 'label')][text()='PART TIME']/following-sibling::*").get()
        duration_full = None
        duration_part = None
        if full_time:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       full_time, re.I | re.M | re.DOTALL)
        if part_time:
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       part_time, re.I | re.M | re.DOTALL)
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

        dom_fee = response.xpath("//div[contains(@class, 'col-sm-6')][contains(*/*/text(), 'Fees and "
                                 "delivery')]/following-sibling::*[1]//div[@class='tabs__content']/div[contains(@id, "
                                 "'panel0')]").getall()
        if dom_fee:
            dom_fee = ''.join(dom_fee)
            dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//div[contains(@class, 'col-sm-6')][contains(*/*/text(), 'Fees and "
                                 "delivery')]/following-sibling::*[1]//div[@class='tabs__content']/div[contains(@id, "
                                 "'panel1')]").getall()
        if int_fee:
            int_fee = ''.join(int_fee)
            int_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["domesticFeeAnnual"] = max(int_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        career1 = response.xpath("//div[contains(@class, 'component--title')][*/text()='Your "
                                 "career']/following-sibling::*/*").getall()
        career2 = response.xpath("//*[@class='tile-carousel__text']").getall()[1:]
        holder = []
        if career1:
            holder.extend(career1)
        if career2:
            holder.extend(career2)
        if holder:
            course_item['careerPathways'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath("//*[@class='tile-carousel__text']").get()
        campus_holder = []
        study_holder = []
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
            if re.search('online', location, re.I | re.M):
                study_holder.append('Online')
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)
            study_holder.append('In Person')
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        yield course_item
