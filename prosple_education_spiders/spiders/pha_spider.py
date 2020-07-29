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


class PhaSpiderSpider(scrapy.Spider):
    name = 'pha_spider'
    allowed_domains = ['www.phoenix.wa.edu.au', 'phoenix.wa.edu.au']
    start_urls = ['https://www.phoenix.wa.edu.au/courses']
    banned_urls = ['https://www.phoenix.wa.edu.au/courses/online-courses']
    institution = 'Phoenix Academy'
    uidPrefix = 'AU-PHA-'

    campuses = {
        "Perth": "30921"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "the certificate iv": "4",
        "certificate iv": "4",
        "foundation studies – certificate iv": "4",
        "phoenix tesol certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
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
        "Dec": "12",
        "Monday": "01|02|03|04|05|06|07|08|09|10|11|12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//li/a[@rel='bookmark']/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//section[@class='content']/h1/text()").get()
        course_code = re.findall('\([A-Z]+\s?[\d]+\s?\)', course_name)
        if course_code:
            course_name = re.sub(course_code[0], '', course_name)
            course_name = re.sub('\(\)', '', course_name)
            course_item['courseCode'] = re.sub('[\(\)]', '', course_code[0]).strip()
        if 'courseCode' not in course_item:
            course_code = response.xpath(
                "//div[@class='top-info']/*[contains(text(), 'National Course')]/*/text()").getall()
            if course_code:
                course_code = "".join(course_code)
                course_code = re.findall('[0-9A-Z]+', course_code)
                if course_code:
                    course_item['courseCode'] = ', '.join(course_code)
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='course-des']/*").getall()
        holder = []
        for item in overview:
            if not re.search('fasc-button', item, re.M):
                if not re.search('<img', item, re.M):
                    holder.append(item)
        if holder:
            if holder[0] in ['<p><strong>Our Value Proposition to You</strong></p>',
                '<p><strong>Partnering with you in Global Leadership and Business Communication</strong></p>']
                course_item.set_summary(strip_tags(holder[1]))
            else:
                course_item.set_summary(strip_tags(holder[0]))
            course_item["overview"] = strip_tags(''.join(holder), False)

        duration = response.xpath("//div[@class='top-info']/*[starts-with(text(), 'Course')]/*/text()").getall()
        if not duration:
            duration = response.xpath("//div[@class='top-info']/*[contains(text(), 'Duration')]/*/text()").getall()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
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
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        cricos = response.xpath("//div[@class='top-info']/*[contains(text(), 'CRICOS Code')]/*/text()").getall()
        if cricos:
            cricos = "".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ', '.join(cricos)
                course_item['internationalApps'] = 1
                course_item['internationalApplyURL'] = response.request.url

        intake = response.xpath("//div[@class='top-info']/*[contains(text(), 'Commencement dates')]/*/text()").getall()
        if not intake:
            intake = response.xpath(
                "//div[@class='top-info']/*[contains(text(), 'Dates')]/*/text()").getall()
        if intake:
            intake = "".join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        study = response.xpath("//div[@class='top-info']/*[contains(text(), 'Delivery Mode')]/*/text()").getall()
        if study:
            study = ''.join(study)
            study_holder = set()
            if re.search('face', study):
                study_holder.add('In Person')
            if re.search('online', study):
                study_holder.add('Online')
            if re.search('both', study):
                study_holder.add('In Person')
                study_holder.add('Online')
            if re.search('blended', study):
                study_holder.add('In Person')
                study_holder.add('Online')
            if study_holder:
                course_item['modeOfStudy'] = '|'.join(study_holder)

        entry = response.xpath("//*[contains(text(), 'Entry requirements')]/following-sibling::*/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), False)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        course_item['campusNID'] = self.campuses['Perth']
        course_item['group'] = 23
        course_item['canonicalGroup'] = 'StudyPerth'

        yield course_item
