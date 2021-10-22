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


class NaveSpiderSpider(scrapy.Spider):
    name = 'nave_spider'
    start_urls = ['http://www.navitasenglish.edu.au/courses/general-english/',
                  'http://www.navitasenglish.edu.au/courses/academic-english/',
                  'http://www.navitasenglish.edu.au/courses/test-preparation-courses/ielts-preparation/',
                  'http://www.navitasenglish.edu.au/courses/test-preparation-courses/cambridge-preparation/']
    institution = "Navitas English"
    uidPrefix = "AU-NAVE-"

    degrees = {
        "graduate certificate": "7",
        "online graduate certificate": "7",
        "graduate diploma": "8",
        "online graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "online master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "phd": "6",
        "certificate": "4",
        "vce": "4",
        "undergraduate certificate": "4",
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
        "North Metropolitan TAFE Perth": "30917",
        "Sydney Hyde Park": "30919",
        "Perth": "30918",
        "Manly Beach": "30916",
        "Darwin": "30915",
        "Brisbane": "30914",
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
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//h1/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search('^<p', item) and not re.search('^<ul', item) and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            course_item.set_summary(strip_tags(holder[0]))
            course_item['overview'] = strip_tags(''.join(holder), False)

        entry = response.xpath("//strong[contains(text(), 'Entry level')]/following-sibling::p").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), False)

        duration = response.xpath("//strong[contains(text(), 'Course duration')]/following-sibling::span").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?full.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?part.time)",
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
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        study = response.xpath("//p[contains(strong/text(), 'Mode of study')]/following-sibling::p").get()
        if study:
            study_holder = set()
            if re.search('myStudy', study, re.I | re.M):
                study_holder.add('Online')
            if re.search('face.to.face', study, re.I | re.M):
                study_holder.add('In Person')
            if study_holder:
                course_item['modeOfStudy'] = '|'.join(study_holder)

        location = response.xpath("//div[contains(strong/text(), 'Next course dates')]").get()
        if location:
            campus_holder = set()
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if campus_holder:
                course_item['campusNID'] = '|'.join(campus_holder)

        cricos = response.xpath("//p[contains(text(), 'CRICOS COURSE CODE')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ', '.join(cricos)
                course_item['internationalApps'] = 1

        learn = response.xpath("//*[contains(text(), 'Your learning outcomes')]/following-sibling::*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), False)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
