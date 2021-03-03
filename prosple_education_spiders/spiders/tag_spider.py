# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


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


class TagSpiderSpider(scrapy.Spider):
    name = 'tag_spider'
    start_urls = ['https://www.tafegippsland.edu.au/course_search?profile=_default&collection=fed-training-meta&query=']
    banned_urls = ['https://www.tafegippsland.edu.au/courses/find_a_course/courses/courses_by_department'
                   '/short_courses_for_individuals/koorie/koorie_workshops']
    institution = "TAFE Gippsland"
    uidPrefix = "AU-TAG-"

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
        "victorian certificate": "9",
        "non-award": "13",
        "no match": "15"
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

    campuses = {
        "Bairnsdale": "59016",
        "Forestec": "59017",
        "Lakes Entrance Seamec": "59018",
        "Leongatha": "59019",
        "Morwell": "59020",
        "Sale (Fulham)": "59021",
        "Sale (FLC)": "59022",
        "Sale (Gtec)": "59023",
        "Traralgon": "59024",
        "Warragul": "59025",
        "Yallourn": "59026",
        "Workplace": "59027",
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
        courses = response.xpath("//ul[@id='search-results']//div[contains(@id, 'result')]/a/@href").getall()
        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//a[@rel='next']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            if re.search('\(Master', course_name):
                course_name = re.sub('\s\(.*', '', course_name, re.DOTALL)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='course-description']/*").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search('^<(p|u|o)', item) and index != 0 and index != 1:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
        if 'overview' not in course_item:
            overview = response.xpath("//div[@class='content-container']//div[@class='editable-content']/div["
                                      "contains(@id, 'content_container')]/*").getall()
            holder = []
            for index, item in enumerate(overview):
                if re.search('<strong', item) and index != 0:
                    break
                elif not re.search('<strong', item):
                    holder.append(item)
            if holder:
                summary = [strip_tags(x) for x in holder]
                course_item.set_summary(' '.join(summary))
                course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath("//div[contains(text(), 'Location')]/following-sibling::*").get()
        campus_holder = set()
        if location:
            location = '|'.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        intake = response.xpath("//div[contains(text(), 'Starting Date')]/following-sibling::*").get()
        if intake:
            holder = []
            for item in self.months.values():
                if re.search('/' + item + '/', intake, re.M):
                    holder.append(item)
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        career = response.xpath("//*[text()='Career Opportunities' or contains(strong/text(), 'Participants will "
                                "learn a range of skills')]/following-sibling::*").get()
        if career:
            course_item['careerPathways'] = strip_tags(career, False, True)

        entry = response.xpath(
            "//*[contains(strong/text(), 'Mandatory entry requirements')]/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(entry):
            if not re.search('^<(p|u|o)', item) and index != 0:
                break
            elif re.search('<strong', item) and index != 0:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            course_item['entryRequirements'] = strip_tags(''.join(holder), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        study = response.xpath("//div[contains(text(), 'Study Mode')]/following-sibling::*").get()
        holder = set()
        if study:
            if re.search('on.campus', study, re.M | re.DOTALL):
                holder.add('In Person')
            if re.search('online', study, re.M | re.DOTALL):
                holder.add('Online')
        if holder:
            course_item['modeOfStudy'] = '|'.join(holder)

        duration = response.xpath("//div[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(?<=full.time.\s)(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M |
                                       re.DOTALL)
            duration_part = re.findall("(?<=part.time.\s)(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M |
                                       re.DOTALL)
            if not duration_full:
                duration_full = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)", duration,
                    re.I | re.M | re.DOTALL)
            if not duration_part:
                duration_part = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)", duration,
                    re.I | re.M | re.DOTALL)
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
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by", "Of"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
