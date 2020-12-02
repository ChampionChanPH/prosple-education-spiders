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


class MuSpiderSpider(scrapy.Spider):
    name = 'mu_spider'
    start_urls = ['https://www.massey.ac.nz/massey/learning/programme-course/programme-list.cfm']
    banned_urls = []
    institution = 'Massey University'
    uidPrefix = 'NZ-MU-'

    campuses = {
        "Auckland": "52524",
        "Manawatū": "52525",
        "Wellington": "52526",
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "foundation certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
        'te aho paerewa postgraduate diploma': '8',
        'postgraduate diploma': '8',
        'postgraduate certificate': '7',
        'te aho tātairangi: bachelor': bachelor_honours
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//div[@id='prog-list']//a")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='overview pp-block pp-keyfacts']/following-sibling::*["
                                  "@class='overview pp-block']/*").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search('^<(p|u|o)', item) and index != 0:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//div[@class='overview pp-block pp-keyfacts']/following-sibling::*[@class='overview "
                               "pp-block']/*[contains(text(), 'What will you learn')]/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(learn):
            if not re.search('^<(p|u|o)', item) and index != 0:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            course_item['whatLearn'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//div[@class='overview pp-block pp-keyfacts']//*[*/text("
                                  ")='Duration']/following-sibling::*").get()
        if duration:
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
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        location = response.xpath("//div[@class='overview pp-block pp-keyfacts']//*[*/text("
                                  ")='Campus']/following-sibling::*").get()
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if re.search('distance learning', location, re.I | re.M):
                study_holder.add('Online')
        online = response.xpath("//div[@class='overview pp-block pp-keyfacts']//*[*/text()='Distance "
                                "learning']/following-sibling::*").get()
        if online and re.search('(?<!un)available', online, re.I | re.M):
            study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        career = response.xpath("//*[@class='accordion-content']/*[text()='Careers']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(career):
            if not re.search('^<(p|u|o)', item) and index != 0:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            course_item['careerPathways'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath("//*[text()='Prior learning, credit and exemptions']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(credit):
            if not re.search('^<(p|u|o)', item) and index != 0:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            course_item['creditTransfer'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//*[@class='accordion-heading'][*/text()='Programme "
                               "admission']/following-sibling::*/*[text()='Required']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(entry):
            if not re.search('^<(p|u|o)', item) and index != 0:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            course_item['entryRequirements'] = strip_tags(''.join(holder), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        check_int_1 = response.xpath("//*[@class='accordion-heading']/*[text()='International students']").getall()
        check_int_2 = response.xpath("//div[@class='overview pp-block pp-keyfacts']//*[*/text("
                                     ")='International']/following-sibling::*").get()
        if check_int_1 or (check_int_2 and re.search('(?<!un)available', check_int_2, re.I | re.M)):
            course_item["internationalApps"] = 1

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        course_item['group'] = 2
        course_item['canonicalGroup'] = 'GradNewZealand'

        yield course_item
