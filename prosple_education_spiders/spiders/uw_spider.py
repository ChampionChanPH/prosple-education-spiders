# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by: Christian Anasco on 28th Apr 2021

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


class UwSpiderSpider(scrapy.Spider):
    name = 'uw_spider'
    allowed_domains = ['www.waikato.ac.nz']
    start_urls = ['https://www.waikato.ac.nz/study/qualifications']
    banned_urls = [
        "qualifications/conjoint-degree",
        "qualifications/individual-paper-credit",
        'qualifications/pathways-programmes',
        'qualifications/certificate',
    ]
    institution = "University of Waikato"
    uidPrefix = "NZ-UW-"

    degrees = {
        "postgraduate certificate": "7",
        "graduate certificate": "7",
        "executive graduate certificate": "7",
        "postgraduate diploma": "8",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "undergraduate certificate": "4",
        "university certificate": "4",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "international diploma": "5",
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
        "Tauranga": "49145",
        "Hamilton": "49144",
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
        courses = response.xpath("//a[@class='course-finder__result-title']/@href").getall()
        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

        # for card in course_cards: summary = card.css("div.course-finder__result-description p").getall() if
        # summary: summary = re.sub("<.*?>", "", summary[-1]) name = card.css("h3::text").get() code = card.css(
        # "li.course-finder__result-code::text").get() course = card.css("a.course-finder__result-title::attr(
        # href)").get() course = response.urljoin(course) if course not in self.blacklist_urls and course not in
        # self.scraped_urls: if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(
        # self.superlist_urls) == 0: self.scraped_urls.append(course) yield response.follow(course,
        # callback=self.course_parse, meta={"summary": summary, "name": name, "code": code})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='header__title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//h1[@class='header__title']/span/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        summary = response.xpath("//div[@class='lead']/*").getall()
        if summary:
            summary = [strip_tags(x) for x in summary]
            course_item.set_summary(' '.join(summary))

        overview = response.xpath("//div[@id='intro-blurb']/*[not(@class)]").getall()
        if overview:
            if 'overviewSummary' not in course_item:
                summary = [strip_tags(x) for x in overview]
                course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        if 'overview' not in course_item and 'overviewSummary' in course_item:
            course_item['overview'] = course_item['overviewSummary']

        if 'overview' not in course_item:
            overview = response.xpath("//section[@id='content']/div[@class='clearfix']/*").getall()
            holder = []
            for index, item in enumerate(overview):
                if re.search('^<(p|u|o)', item) and re.search('#success-stories', item):
                    pass
                elif re.search('^<(p|u|o)', item):
                    holder.append(item)
                elif index == 0:
                    pass
                else:
                    break
            if holder:
                summary = [strip_tags(x) for x in holder]
                course_item.set_summary(' '.join(summary))
                course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        period = response.xpath("//table[contains(@class, 'key-info-table')]//tr[1]/th[contains(text(), 'Year') or "
                                "contains(text(), 'Week') or contains(text(), 'Month') or contains(text(), "
                                "'Duration Of Study')]/text()").get()
        if period:
            num = response.xpath("//table[contains(@class, 'key-info-table')]//tr[1]/th[contains(text(), 'Year') or "
                                 "contains(text(), 'Week') or contains(text(), 'Month') or contains(text(), "
                                 "'Duration Of Study')]/following-sibling::td/text()").get()
            if num:
                duration = num + ' ' + period

                duration_full = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?\(full)",
                    duration, re.I | re.M | re.DOTALL)
                duration_part = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?\(part)",
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

        location = response.xpath("//table[contains(@class, 'key-info-table')]//th[contains(text(), 'Study "
                                  "Locations:')]/following-sibling::*").get()
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

        intake = response.xpath("//table[contains(@class, 'key-info-table')]//th[contains(text(), 'Start "
                                "Dates:')]/following-sibling::*").get()
        if not intake:
            intake = response.xpath("//section[@id='content']/div[@class='clearfix']/*").getall()
            intake = ''.join(intake)
        holder = []
        if intake:
            for month in self.months:
                if re.search(month, intake, re.M):
                    holder.append(self.months[month])
        if holder:
            course_item["startMonths"] = "|".join(holder)

        dom_fee = response.xpath("//table[contains(@class, 'key-info-table')]//th[contains(text(), 'Fees ("
                                 "Domestic):')]/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//table[contains(@class, 'key-info-table')]//th[contains(text(), 'Fees ("
                                 "International):')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        career = response.xpath("//*[contains(text(), 'Career opportunities')]/following-sibling::*").getall()
        if career:
            course_item['careerPathways'] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//*[contains(text(), 'Entry requirements')]/following-sibling::*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item["group"] = 2
        course_item["canonicalGroup"] = "GradNewZealand"

        yield course_item



