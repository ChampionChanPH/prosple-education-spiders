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


class KcbtSpiderSpider(scrapy.Spider):
    name = 'kcbt_spider'
    start_urls = ['https://kcbt.wa.edu.au/category/courses/']
    banned_urls = []
    institution = 'Keystone College of Business and Technology'
    uidPrefix = 'AU-KCBT-'

    campuses = {
        "Adelaide": "30911",
        "Perth": "30910"
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
        "double diplomas: diploma": "5",
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
        courses = response.xpath("//h2/a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='chead']/text()").get()
        course_name = re.sub("[-–]", "", course_name)
        course_code = ''
        name = ''
        if course_name.strip() not in ['PTE', 'IELTS', 'FCE / CAE']:
            name = course_name
            course_code = re.findall('[0-9A-Z]{8,}', course_name)
        for item in course_code:
            name = re.sub(item, '', name)
        if course_code:
            course_item['courseCode'] = ''.join(course_code)
        if name.strip() == '':
            course_item.set_course_name(course_name.strip(), self.uidPrefix)
        else:
            course_item.set_course_name(name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//div[contains(@class, 'c-block')][1]//div[@class='tve_shortcode_rendered']/p[1]").getall()
        if not overview:
            overview = response.xpath("//div[contains(@class, 'c-block')][1]/*").getall()
        holder = []
        for item in overview:
            if re.search("^<p", item):
                holder.append(item)
        if holder:
            course_item.set_summary(strip_tags(holder[0]))
            course_item["overview"] = strip_tags(''.join(holder), False)

        entry = response.xpath("//*[contains(text(), 'Entry Requirements')]/following-sibling::*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(''.join(entry), False)

        credit = response.xpath("//*[contains(text(), 'Recognition of Prior Learning')]/following-sibling::*").getall()
        if credit:
            course_item["creditTransfer"] = strip_tags(''.join(credit), False)

        career = response.xpath(
            "//*[contains(text(), 'Study Pathway and Career Opportunities')]/following-sibling::*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(''.join(career), False)

        cricos = response.xpath("//h5/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        course_item['campusNID'] = '30910|30911'
        course_item['group'] = 23
        course_item['canonicalGroup'] = 'StudyPerth'

        yield course_item


