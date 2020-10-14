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


class TatSpiderSpider(scrapy.Spider):
    name = 'tat_spider'
    start_urls = ['https://www.tastafe.tas.edu.au/courses']
    institution = "TAFE Tasmania"
    uidPrefix = "AU-TAT-"

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
        "Alanvale": "55686",
        "Hunter Street": "55687",
        "Burnie": "55688",
        "Campbell Street": "55689",
        "Devonport": "55690",
        "Clarence": "55691",
        "Bender Drive": "55692",
        "Drysdale Hobart": "55693",
        "Drysdale Launceston": "55694",
        "Launceston": "55695",
        "Inveresk": "55696",
        "Claremont": "55697"
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

    all_terms = get_terms()

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//*[text()='Browse by industry']/following-sibling::ul//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.link_parse)

    def link_parse(self, response):
        courses = response.xpath("//div[@class='courses-results']//*[@class='course-result__title']/a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//a[contains(@class, 'pagination__link--next')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.link_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//*[contains(@class, 'overview-title')]/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//*[contains(@class, 'overview-id')]/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        holder = []
        summary = response.xpath("//div[@class='pb4']/h3").get()
        if summary:
            holder.append(summary)
            course_item.set_summary(strip_tags(summary))

        overview = response.xpath("//div[@class='pb4']/h3/following-sibling::*/*").getall()
        for item in overview:
            if re.search('^<p', item) or re.search('^<ul', item) or re.search('^<ol', item):
                holder.append(item)
        if holder:
            course_item["overview"] = strip_tags(''.join(holder), False)

        entry = response.xpath(
            "//a[text()='Entry']/following-sibling::*[1]//*[self::p or self::ul or self::ol]").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), False)

        credit = response.xpath("//a[text()='Recognition of prior learning and skills']/following-sibling::*[1]//*["
                                "self::p or self::ul or self::ol]").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(''.join(credit), False)

        career = response.xpath("//*[text()='Career opportunities']/following-sibling::*").get()
        if career:
            course_item['careerPathways'] = strip_tags(career, False)

        location = response.xpath("//*[text()='Locations']/following-sibling::*").getall()
        campus_holder = set()
        study_holder = set()
        if location:
            location = ''.join(location)
            for campus in self.campuses:
                if campus == 'Launceston':
                    if re.search('(?<!Drysdale )Launceston', location, re.I):
                        campus_holder.add(self.campuses[campus])
                elif re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if re.search('online', location, re.I):
                study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        dom_fee = response.xpath("//*[text()='Commercial']/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            if dom_fee:
                course_item["domesticFeeAnnual"] = float(''.join(dom_fee[0]))
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//*[text()='Subsidised']/following-sibling::*").get()
        if csp_fee:
            csp_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            if csp_fee:
                course_item["domesticSubFeeAnnual"] = float(''.join(csp_fee[0]))
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        update_matches(course_item, self.all_terms)

        yield course_item
