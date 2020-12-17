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


class LtuSpiderSpider(scrapy.Spider):
    name = 'ltu_spider'
    start_urls = [
        'https://www.latrobe.edu.au/handbook/2021/undergraduate/',
        # 'https://www.latrobe.edu.au/handbook/2021/postgraduate/',
        # 'https://www.latrobe.edu.au/handbook//2021/postgraduate/research.htm',
    ]
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    institution = 'La Trobe University'
    uidPrefix = 'AU-LTU-'

    custom_settings = {
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    }

    campuses = {
        "North Campus": "53669",
        "City Campus": "53670",
        "South Campus": "53671",
        "Distance": "53672"
    }

    degrees = {
        "graduate certificate": "7",
        "postgraduate certificate": "7",
        "graduate diploma": "8",
        "postgraduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "senior executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "doctoral program": "6",
        "certificate": "4",
        "specialist certificate": "4",
        "professional certificate": "14",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "juris doctor": "10",
        "joint doctor": "6",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        for index, item in enumerate(self.start_urls):
            if item == self.start_urls[2]:
                yield response.follow(response.request.url, callback=self.graduate_research_parse)
            else:
                yield response.follow(response.request.url, callback=self.undergraduate_and_postgraduate_parse)

    def graduate_research_parse(self, response):
        links = response.xpath("//*[@class='content']//a")
        yield from response.follow_all(links, callback=self.course_parse)

    def undergraduate_and_postgraduate_parse(self, response):
        links = response.xpath("//*[@class='linkList']/*[@class='sectionHeading'][not(contains(text(), "
                               "'Campuses'))]/following-sibling::*//a/@href").getall()
        if links:
            for item in links:
                yield response.follow(item, callback=self.undergraduate_and_postgraduate_parse)
        else:
            yield response.follow(response.request.url, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        # location = response.xpath("//select[@id='selected-course-campus']/option/text()").getall()
        # if location:
        #     course_item['campusNID'] = '|'.join(location)
        #
        # overview = response.xpath("//div[@class='book-one-on-one hide-pdf']/following-sibling::*[not("
        #                           "@class='hide-pdf')][1]/*").getall()
        # if overview:
        #     summary = [strip_tags(x) for x in overview]
        #     course_item.set_summary(' '.join(summary))
        #     course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)
        #
        # atar = response.xpath("//*[@id='atar-content']").get()
        # if atar:
        #     atar = re.findall('\d{2}\.\d{2}', atar, re.M)
        #     atar = [float(x) for x in atar]
        #     if len(atar) == 1:
        #         course_item['guaranteedEntryScore'] = atar[0]
        #     if len(atar) == 2:
        #         course_item['lowestScore'] = min(atar)
        #         course_item['guaranteedEntryScore'] = max(atar)
        #
        # intake = response.xpath("//div[contains(@class, 'mock-table-cell')][contains(text(), 'Start') and contains("
        #                         "text(), 'dates')]/following-sibling::*").get()
        # start_holder = []
        # for item in self.months:
        #     if re.search(item, intake, re.M):
        #         start_holder.append(self.months[item])
        # if start_holder:
        #     course_item['startMonths'] = '|'.join(start_holder)
        #
        # duration = response.xpath(
        #     "//div[contains(@class, 'mock-table-cell')][text()='Duration']/following-sibling::*").get()
        # if duration:
        #     duration_full = re.findall(
        #         "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
        #         duration, re.I | re.M | re.DOTALL)
        #     duration_part = re.findall(
        #         "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
        #         duration, re.I | re.M | re.DOTALL)
        #     if not duration_full and duration_part:
        #         self.get_period(duration_part[0][1].lower(), course_item)
        #     if duration_full:
        #         course_item["durationMinFull"] = float(duration_full[0][0])
        #         self.get_period(duration_full[0][1].lower(), course_item)
        #     if duration_part:
        #         if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
        #             course_item["durationMinPart"] = float(duration_part[0][0])
        #         else:
        #             course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
        #                                              / self.teaching_periods[duration_part[0][1].lower()]
        #     if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
        #         duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
        #                                    duration, re.I | re.M | re.DOTALL)
        #         if duration_full:
        #             # course_item["durationMinFull"] = float(duration_full[0][0])
        #             # self.get_period(duration_full[0][1].lower(), course_item)
        #             if len(duration_full) == 1:
        #                 course_item["durationMinFull"] = float(duration_full[0][0])
        #                 self.get_period(duration_full[0][1].lower(), course_item)
        #             if len(duration_full) == 2:
        #                 course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
        #                 course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
        #                 self.get_period(duration_full[1][1].lower(), course_item)
        #
        # dom_fee = response.xpath("//div[contains(@class, 'mock-table-cell')][contains(text(), 'Fees') and contains("
        #                          "text(), 'scholarships')]/following-sibling::*").get()
        # if not dom_fee:
        #     dom_fee = response.xpath("//div[contains(@class, 'mock-table-cell')][contains(text(), 'Annual') and "
        #                              "contains(text(), 'tuition')]/following-sibling::*").get()
        # if dom_fee:
        #     dom_fee = re.findall("\$(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
        #     dom_fee = [float(''.join(x)) for x in dom_fee]
        #     if dom_fee:
        #         course_item["domesticFeeAnnual"] = max(dom_fee)
        #         get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
        #
        # career = response.xpath("//*[@class='section-heading'][text()='Career outcomes']/following-sibling::*").getall()
        # holder = []
        # for item in career:
        #     if not re.search('^<(p|o|u|h)', item):
        #         break
        #     else:
        #         holder.append(item)
        # if holder:
        #     course_item['careerPathways'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
        #
        # cricos = response.xpath(
        #     "//div[contains(@class, 'mock-table-cell')][text()='CRICOS']/following-sibling::*").get()
        # if cricos:
        #     cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
        #     if cricos:
        #         course_item["cricosCode"] = ", ".join(cricos)
        #         course_item["internationalApps"] = 1
        #
        # course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
