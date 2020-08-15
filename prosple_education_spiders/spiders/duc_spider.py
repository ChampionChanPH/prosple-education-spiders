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


class DucSpiderSpider(scrapy.Spider):
    name = 'duc_spider'
    start_urls = ['https://www.ducere.edu.au/courses/']
    banned_urls = []
    institution = 'Ducere Global Business School'
    uidPrefix = 'AU-DUC-'

    campuses = {
        "Victoria": "35122"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "mba": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "juris doctor": "10",
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
        courses = response.xpath("//div[@class='products']/div[contains(@class, 'wtrContainerColor')]//div[contains("
                                 "@class, 'program-name')]/a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse, meta={'duration': duration, 'study': study})

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//div[contains(@class, 'dhvc_woo_product-meta-field-course_title')]/text()").get()
        if course_name:
            if re.search("MBA", course_name):
                name = re.sub("\(", "- ", course_name)
                name = re.sub("\)", "", name)
                course_item.set_course_name(name.strip(), self.uidPrefix)
            else:
                course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='vc_empty_space  desktoponly']/following-sibling::*").getall()
        holder = []
        for item in overview:
            if not re.search("^<p", item):
                break
            elif re.search("Course Learning Outcomes", item):
                break
            else:
                holder.append(item)
        if holder:
            course_item['overview'] = strip_tags(''.join(holder), False)

        summary = response.xpath("//div[contains(@class, 'dhvc_woo_product-meta-field-course_info')]/text()").get()
        if not summary and holder:
            summary = holder[0]
        if summary:
            course_item.set_summary(strip_tags(summary.strip()))

        start = response.xpath("//div[contains(*//text(), 'Intake Dates')]").getall()
        start_holder = []
        if start:
            start = ''.join(start)
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
        if start_holder:
            course_item['startMonths'] = '|'.join(start_holder)

        learn = response.xpath("//*[contains(text(), 'You will') or contains(strong/text(), 'You will') or contains("
                               "strong/text(), 'Course Learning Outcomes')]/following-sibling::*[self::ul or "
                               "self::ol]").get()
        if learn:
            course_item['whatLearn'] = strip_tags(learn, False)

        entry = response.xpath(
            "//div[contains(@class, 'dhvc_woo_product-meta-field-course_requirements')]/text()").getall()
        holder = []
        for item in entry:
            holder.append('<li>' + item.strip() + '</li>')
        if holder:
            course_item['entryRequirements'] = '<ul>' + ''.join(holder) + '</ul>'

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', '-'])

        course_item.set_course_name(course_name.strip(), self.uidPrefix)

        if course_item['courseName'] == 'Bachelor of Applied Entrepreneurship':
            course_item['domesticFeeTotal'] = 46200
            course_item['creditTransfer'] = '''You may be able to get credit or RPL for some units of this course 
                        based on your previous education and work experience. This means the duration of the course may be 
                        reduced. Applicants are advised to contact the degree administrator. '''
            course_item['durationMinFull'] = 2
            course_item['durationMaxPart'] = 4
            course_item['teachingPeriod'] = 1
            course_item['modeOfStudy'] = 'Online'
        elif course_item['courseName'] == 'Bachelor of Applied Business (Marketing)':
            course_item['domesticFeeTotal'] = 46200
            course_item['creditTransfer'] = '''You may be able to get credit or RPL for some units of this course 
                        based on your previous education and work experience. This means the duration of the course may be 
                        reduced. Applicants are advised to contact the degree administrator. '''
            course_item['durationMinFull'] = 2
            course_item['durationMaxPart'] = 4
            course_item['teachingPeriod'] = 1
            course_item['modeOfStudy'] = 'Online'
        elif course_item['courseName'] == 'Master of Business Administration (Innovation and Leadership)':
            course_item['durationMinFull'] = 1.25
            course_item['durationMaxPart'] = 3
            course_item['teachingPeriod'] = 1
            course_item['modeOfStudy'] = 'Online|In Person'
        elif course_item['courseName'] == 'Graduate Certificate - Data & Cyber Management':
            course_item['domesticFeeTotal'] = 10800
            course_item['creditTransfer'] = '''You may be able to get credit or RPL for some units of this course 
                        based on your previous education and work experience. This means the duration of the course may be 
                        reduced. Applicants are advised to contact the degree administrator. '''
            course_item['durationMinFull'] = 0.5
            course_item['durationMaxPart'] = 2
            course_item['teachingPeriod'] = 1
            course_item['modeOfStudy'] = 'Online'
        elif course_item['courseName'] == 'MBA (Data & Cyber Management)':
            course_item['domesticFeeTotal'] = 32400
            course_item['durationMinFull'] = 1
            course_item['durationMaxPart'] = 2
            course_item['teachingPeriod'] = 1
            course_item['modeOfStudy'] = 'Online'
        elif course_item['courseName'] == 'Bachelor of Applied Business (Management)':
            course_item['domesticFeeTotal'] = 46200
            course_item['creditTransfer'] = '''You may be able to get credit or RPL for some units of this course 
                        based on your previous education and work experience. This means the duration of the course may be 
                        reduced. Applicants are advised to contact the degree administrator. '''
            course_item['durationMinFull'] = 2
            course_item['durationMaxPart'] = 4
            course_item['teachingPeriod'] = 1
            course_item['modeOfStudy'] = 'Online'

        yield course_item




