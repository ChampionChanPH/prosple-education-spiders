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


class TasSpiderSpider(scrapy.Spider):
    name = 'tas_spider'
    start_urls = ['https://www.tafesa.edu.au/courses/']
    institution = "TAFE SA"
    uidPrefix = "AU-TAS-"

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
        "diploma program": "5",
        "dual diploma program": "5",
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
        categories = response.xpath("//*[contains(text(), 'Course Areas')]/following-sibling::*["
                                    "@class='grid_mainContent']//ul//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[@class='areas_of_study']//a/@href").getall()

        for item in sub:
            yield response.follow(item, callback=self.link_parse)

    def link_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'study_area_course_list')]//tr//a/@href").getall()
        courses = set([re.sub('(?<=aspx).*', '', x) for x in courses])

        for item in courses:
            if re.search('/xml/', item):
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='cp_title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[@id='CourseDescription']").getall()
        if overview:
            overview = ''.join(overview)
            course_item.set_summary(strip_tags(overview))
            course_item["overview"] = strip_tags(overview, False)

        career = response.xpath("//h3[contains(text(), 'Employment Outcomes')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if re.search('^<p', item) or re.search('^<ul', item) or re.search('^<ol', item):
                holder.append(item)
            else:
                break
        if holder:
            course_item["careerPathways"] = strip_tags(''.join(holder), False)

        course_code = response.xpath("//*[@class='course-codes']/*[@class='tafesa-code']/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        dom_fee = response.xpath("//div[contains(text(), 'Full Fee') or contains(*/text(), 'Full "
                                 "Fee')]/following-sibling::*[last()]").get()
        if dom_fee:
            dom_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            if dom_fee:
                dom_fee = [float(''.join(x)) for x in dom_fee]
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//div[contains(text(), 'Subsidised') or contains(*/text(), "
                                 "'Subsidised')]/following-sibling::*[last()]").get()
        if csp_fee:
            csp_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            if csp_fee:
                csp_fee = [float(''.join(x)) for x in csp_fee]
                course_item["domesticSubFeeAnnual"] = max(csp_fee)
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        location = response.xpath("//a[contains(@title, 'campus information')]/text()").getall()
        if location:
            location = ' - '.join(location)
            course_item['campusNID'] = location

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        update_matches(course_item, self.all_terms)

        int_link = response.xpath("//div[@class='intake_tab-wrapper']/a[text()='International']/@href").get()
        if int_link:
            yield response.follow(int_link, callback=self.international_parse, meta={'item': course_item})
        elif re.search('/in/', course_item['sourceURL']):
            yield response.follow(course_item['sourceURL'], callback=self.international_parse, meta={'item': course_item})
        else:
            yield course_item

    @staticmethod
    def international_parse(response):
        course_item = response.meta['item']

        cricos = response.xpath("//*[@class='course-codes']/*[@class='cricos-code']/text()").get()
        if cricos:
            course_item['cricosCode'] = cricos.strip()
            course_item["internationalApps"] = 1

        int_fee = response.xpath("//div[@class='cp_cell'][contains(text(), 'Total Fees')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            if int_fee:
                int_fee = [float(''.join(x)) for x in int_fee]
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        yield course_item
