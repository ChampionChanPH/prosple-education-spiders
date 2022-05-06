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
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class CucSpiderSpider(scrapy.Spider):
    name = 'cuc_spider'
    start_urls = ['https://www.curtincollege.edu.au/']
    institution = 'Curtin College'
    uidPrefix = 'AU-CUC-'

    campuses = {
        "Curtin Bentley": "30903",
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
        "undergraduate certificate": "4",
        "foundation certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
        'postgraduate diploma': '8',
        'postgraduate certificate': '7',
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
        "December": "12"
    }

    term = {
        'Semester 1': '02',
        'Semester 2': '07',
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath(
            "//a[@class='cmp-globalnavmegamenu__item-link' and contains(span/text(), 'Courses')]/following-sibling::div//li[not(contains(@class, 'cmp-globalnavmegamenu__item-overview') or contains(@class, 'cmp-globalnavmegamenu__item--has-child'))]/a/@href").getall()
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath(
            "//h1[@class='cmp-teaser__title']/text()").get()
        if course_name:
            if re.search("\(", course_name, re.M) and not re.search("Masters Qualifying", course_name, re.M):
                course_name = re.findall("\((.*)\)", course_name)[0]
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//div[contains(@class, 'cmp-sectiontextblock__title') and div//text()='Course overview']/following-sibling::div//div[@class='cmp-description']/*").getall()
        holder = []
        for item in overview:
            if re.search("^<p", item):
                holder.append(item)
            else:
                break
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//div[contains(@class, 'cmp-sectiontextblock__title') and div//text()='Leading to:']/following-sibling::div//div[@class='cmp-description']/*").getall()
        if not career:
            career = response.xpath(
                "//h3[contains(text(), 'Careers include')]/following-sibling::*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath(
            "//div[@class='cmp-keyinformation__subtitle' and div//text()='Duration']/following-sibling::div[contains(@class, 'cmp-keyinformation__description')]/*").get()
        if duration:
            duration_full = re.findall("\(.{0,2}?(\d*\.?\d+)(?=[- ](year|month|semester|trimester|quarter|week|day))",
                                       duration, re.I | re.M | re.DOTALL)
            if len(duration_full) == 1:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if len(duration_full) == 2 and duration_full[0][1] == duration_full[1][1]:
                course_item["durationMinFull"] = float(
                    duration_full[0][0]) + float(duration_full[1][0])
                self.get_period(duration_full[0][1].lower(), course_item)

        start = response.xpath(
            "//div[@class='cmp-keyinformation__subtitle' and div//text()='Intake dates']/following-sibling::div[contains(@class, 'cmp-keyinformation__description')]/*").get()
        if not start:
            start = response.xpath(
                "//div[@class='cmp-keyinformation__subtitle' and div//text()='Intake Dates']/following-sibling::div[contains(@class, 'cmp-keyinformation__description')]/*").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        location = response.xpath(
            "//div[@class='cmp-keyinformation__subtitle' and div//text()='Campus location']/following-sibling::div[contains(@class, 'cmp-keyinformation__description')]/*").get()
        if not location:
            location = response.xpath(
                "//div[@class='cmp-keyinformation__subtitle' and div//text()='Campus Location']/following-sibling::div[contains(@class, 'cmp-keyinformation__description')]/*").get()
        campus_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        cricos = response.xpath(
            "//*[contains(text(), 'CRICOS Code')]").getall()
        if cricos:
            cricos = ''.join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        dom_fee = response.xpath(
            "//div[contains(@class, 'cmp-keyinformation__domestic-fee')]/div[div/*/text()='Fees']/following-sibling::div/div").get()
        if dom_fee:
            dom_fee = re.findall("= \$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = sum(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath(
            "//div[contains(@class, 'cmp-keyinformation__international-fee')]/div[div/*/text()='Fees']/following-sibling::div/div").get()
        if int_fee:
            int_fee = re.findall("= \$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeTotal"] = sum(int_fee)
                # get_total("internationalFeeAnnual",
                #           "internationalFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              "and", "/", ","], type_delims=["of", "in", "by"])

        yield course_item
