# -*- coding: utf-8 -*-
# by: Johnel Bacani
# Updated by: Christian Anasco (05 Jan 2021)

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
                course_item[field_to_update] = float(course_item[field_to_use]) * \
                                               float(course_item["durationMinFull"]) / 12
        if course_item["teachingPeriod"] == 52:
            if float(course_item["durationMinFull"]) < 52:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * \
                                               float(course_item["durationMinFull"]) / 52


class AcnSpiderSpider(scrapy.Spider):
    name = 'acn_spider'
    # allowed_domains = ['https://www.acn.edu.au/education/postgraduate-courses']
    start_urls = ['https://www.acn.edu.au/education/postgraduate-courses']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Australian College of Nursing (ACN)"
    uidPrefix = "AU-ACN-"

    download_delay = 5
    holder = {
        "duration": [],
        "mode": [],
        "months": []
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

    teaching_periods = {
        "year": 1,
        "semester": 2,
        "trimester": 3,
        "quarter": 4,
        "month": 12,
        "week": 52,
        "day": 365
    }

    duration_patterns = {
        "Year Part-time": {"field": "durationMinPart", "period": 1},
        "weeks": {"field": "durationMinFull", "period": 52}
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        #     yield SplashRequest(response.request.url, callback=self.postgrad_catalog, args={'wait': 10})
        #
        # def postgrad_catalog(self, response):
        #     courses = response.xpath("//div[contains(@class, 'standard-arrow')]//li/a/@href").getall()
        courses = response.xpath("//h1[text()='Our Graduate Certificates']/following-sibling::*//li/a")
        # for course in courses:
        #     if course not in self.blacklist_urls and course not in self.scraped_urls:
        #         if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
        #             self.scraped_urls.append(course)
        #             yield SplashRequest(course, callback=self.course_parse, args={'wait': 10}, meta={"url":course})
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_item.set_course_name(response.css("div.uvc-sub-heading::text").get(), self.uidPrefix)
        course_item.set_sf_dt()

        overview = response.xpath(
            "//*[text()='Course overview']/following-sibling::*[2]//*[@class='wpb_wrapper']/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath("//h3/span[contains(text(), 'CRICOS')]/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item['internationalApplyURL'] = response.request.url

        duration = response.xpath("//*[text()='Duration']/following-sibling::*").getall()
        if duration:
            duration = ''.join(duration)
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

        mode = response.xpath("//div[preceding-sibling::h4/text()='Study mode']/div/p/text()").get()
        if mode:
            holder = []
            if "online" in mode.lower():
                holder.append("Online")

            if "face to face" in mode.lower():
                holder.append("In person")
                course_item["campusNID"] = "44194"

            course_item["modeOfStudy"] = "|".join(holder)

        # dom_fee = response.xpath("//*[text()='Fees']/following-sibling::*").getall()
        # if dom_fee:
        #     dom_fee = ''.join(dom_fee)
        #     dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
        #     dom_fee = [float(''.join(x)) for x in dom_fee]
        #     if dom_fee:
        #         course_item["domesticFeeAnnual"] = max(dom_fee)
        #         get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        intake = response.xpath("//div[preceding-sibling::h4/text()='Intakes']/div/p/text()").get()
        if intake:
            holder = []
            for item in self.months:
                if re.search(item, intake, re.I | re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        careerPathways = response.xpath(
            "//div[preceding-sibling::h2/text()='Career outcomes'][2]/div/p/text()").getall()
        if careerPathways:
            course_item["careerPathways"] = strip_tags("<br>".join(careerPathways), remove_all_tags=False,
                                                       remove_hyperlinks=True)

        whatLearn = response.css("#outcomes .standard-arrow").get()
        if not whatLearn:
            whatLearn = response.xpath(
                "//h1[text()='Learning outcomes']/following-sibling::*[contains(@class , 'standard-arrow')]").get()
        if whatLearn:
            course_item["whatLearn"] = strip_tags(whatLearn, remove_all_tags=False, remove_hyperlinks=True)

        entryRequirements = response.css("#requirements .standard-arrow").get()
        if not entryRequirements:
            entryRequirements = response.css("#requirements .wpb_wrapper").get()
        if entryRequirements:
            course_item["entryRequirements"] = strip_tags(entryRequirements, remove_all_tags=False,
                                                          remove_hyperlinks=True)

        courseStructure = response.xpath("//div[preceding-sibling::h2/text()='Units of study'][2]").get()
        if courseStructure:
            course_item["courseStructure"] = strip_tags(courseStructure, remove_all_tags=False, remove_hyperlinks=True)

        yield course_item
