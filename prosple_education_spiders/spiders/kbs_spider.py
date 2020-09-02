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


class KbsSpiderSpider(scrapy.Spider):
    name = 'kbs_spider'
    start_urls = ['https://www.kbs.edu.au/courses/graduate-certificate-in-business-administration',
                  'https://www.kbs.edu.au/courses/graduate-diploma-of-business-administration',
                  'https://www.kbs.edu.au/courses/mba-master-of-business-administration',
                  'https://www.kbs.edu.au/courses/graduate-certificate-in-business-analytics',
                  'https://www.kbs.edu.au/courses/graduate-diploma-of-business-analytics',
                  'https://www.kbs.edu.au/courses/master-of-business-analytics',
                  'https://www.kbs.edu.au/courses/master-of-business-analytics-extension']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Kaplan Business School"
    uidPrefix = "AU-KBS-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "mba - master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
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
        "Perth": "54436"
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

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//ol[@class='breadcrumb']/li[@class='active']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@id='overview']//span[@class='field__item']/*").getall()
        holder = []
        for item in overview:
            if re.search('<img', item):
                break
            elif not re.search('^<p', item):
                break
            else:
                holder.append(item)
        if holder:
            course_item.set_summary(strip_tags(holder[0]))
            course_item['overview'] = strip_tags(''.join(holder), False)

        cricos = response.xpath("//span[contains(@class, 'cricos-code')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ', '.join(cricos)
                course_item['internationalApps'] = 1
                course_item['internationalApplyURL'] = response.request.url

        intake = response.xpath("//div[contains(@class, 'start-date')]").get()
        start_holder = []
        for item in self.months:
            if re.search(item, intake, re.M):
                start_holder.append(self.months[item])
        if start_holder:
            course_item['startMonths'] = '|'.join(start_holder)

        career = response.xpath(
            "//div[contains(@class, 'career-outcomes')]//span[contains(@class, 'field__item')]/text()").getall()
        if career:
            career = ['<li>' + x.strip() + '</li>' for x in career]
            course_item['careerPathways'] = '<ul>' + ''.join(career) + '</ul>'

        career = response.xpath("//div[contains(@id, 'career-outcomes')]//div[@class='field--item']/p").getall()
        if career and 'careerPathways' in course_item:
            course_item['careerPathways'] = course_item['careerPathways'] + ''.join(career)

        credit = response.xpath(
            "//p[contains(*//text(), 'Recognition of prior learning (RPL)')]/following-sibling::*").getall()
        holder = []
        for item in credit:
            if re.search('PDF', item):
                break
            elif not re.search('^<p', item):
                break
            else:
                holder.append(item)
        if holder:
            course_item['creditTransfer'] = strip_tags(''.join(holder), False)

        # entry = response.xpath("//div[@id='entry-requirements']//span[@class='field__item']/*").getall()

        duration = response.xpath("//div[contains(@class, 'typical-duration')]").get()
        if duration:
            duration = strip_tags(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(trimester))",
                                       duration, re.I | re.M | re.DOTALL)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if "durationMinFull" not in course_item:
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

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        course_item['campusNID'] = self.campuses['Perth']
        course_item['group'] = 23
        course_item['canonicalGroup'] = 'StudyPerth'

        yield course_item
