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


class ShcSpiderSpider(scrapy.Spider):
    name = 'shc_spider'
    start_urls = ['https://www.sheridan.edu.au/index.php/study']
    banned_urls = []
    institution = 'Sheridan Institute of Higher Education'
    uidPrefix = 'AU-SHC-'

    campuses = {
        "Perth CBD": "35038",
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

    numbers = {
        "One academic term": '1',
        "One": '1',
        "Two": '2',
        "Three": '3',
        "Four": '4',
        "Five": '5',
        "Six": '6',
        "Seven": '7',
        "Eight": '8',
        "Nine": '9',
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
            "//div[@class='qx-element-blurb__title']/a")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["modeOfStudy"] = "In Person"

        domestic_url = response.xpath(
            "//a[div/span/text()='Domestic']/@href").get()
        if domestic_url:
            course_item["domesticApplyURL"] = domestic_url

        international_url = response.xpath(
            "//a[div/span/text()='International']/@href").get()
        if international_url:
            course_item["internationalApps"] = 1
            course_item["internationalApplyURL"] = international_url

        course_name = response.xpath("//h1/span/text()").get()
        if not course_name:
            course_name = response.xpath("//h2/span/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//div[@id='qx-heading-36241']//span").getall()
        holder = []
        if not overview:
            overview = response.xpath(
                "//h2[@itemprop='headline']/following-sibling::div[@itemprop='articleBody']/*").getall()
            for item in overview:
                if re.search("^<(p|u|o)", item):
                    holder.append(item)
                else:
                    break
        else:
            holder = overview[:]
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//div[@id='course-structure']/*/*").getall()
        if structure:
            course_item["courseStructure"] = strip_tags(
                ''.join(structure[1:]), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath(
            "//div[@id='course-learning-outcomes']/*/*").getall()
        if learn:
            course_item["whatLearn"] = strip_tags(
                ''.join(learn[1:]), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath(
            "//div[@id='course-learning-outcomes']/*/*").getall()
        if duration:
            duration = "".join(duration)
            for num in self.numbers:
                duration = re.sub(num, self.numbers[num], duration)
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
                        course_item["durationMinFull"] = float(
                            duration_full[0][0])
                        self.get_period(
                            duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(
                            duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by', 'for'])

        course_item['group'] = 23
        course_item['canonicalGroup'] = 'StudyPerth'

        yield course_item
