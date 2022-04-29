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


class LtuonlineSpiderSpider(scrapy.Spider):
    name = 'ltuonline_spider'
    start_urls = ['https://onlinecourses.latrobe.edu.au/courses/']
    banned_urls = []
    institution = 'La Trobe University'
    uidPrefix = 'AU-LTU-ON-'

    campuses = {
        "Melbourne": "624",
        "Albury-Wodonga": "629",
        "Bendigo": "632",
        "City": "627",
        "Mildura": "635",
        "Shepparton": "639",
        "Sydney": "626",
        "Bundoora": "628",
    }

    degrees = {
        "graduate certificate": "7",
        "postgraduate certificate": "7",
        "online graduate certificate": "7",
        "graduate diploma": "8",
        "postgraduate diploma": "8",
        "master": research_coursework,
        "mba": research_coursework,
        "online master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "doctoral program": "6",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//a[@class='tux-c-card__link']")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//*[contains(@class, 'tux-c-page-header__heading')]/text()").get()
        if course_name:
            if re.search('online mba', course_name, re.I):
                name = 'Online Master of Business Administration'
            else:
                name = course_name
            course_item.set_course_name(name.strip(), self.uidPrefix)

        holder = []
        summary1 = response.xpath("//h2[contains(@class, 'tux-c-hero__heading')]/text()").get()
        if summary1:
            if not re.search('\.$', summary1):
                holder.append(summary1.strip() + '.')
            else:
                holder.append(summary1.strip())
        summary2 = response.xpath("//h2[contains(@class, 'tux-c-hero__heading')]/following-sibling::*").getall()
        if summary2:
            summary2 = [strip_tags(re.sub('<sup>.*?</sup>', '', x, re.DOTALL)) for x in summary2]
            holder.extend(summary2)
        if holder:
            course_item.set_summary(' '.join(holder))

        overview = response.xpath("//div[@data-label='One Column'][*/*[@class='h3']]/*/*").getall()
        if overview:
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//div[@data-label='Column'][contains(*/*/text(), 'Course "
                               "outcomes')]/following-sibling::*/*/*").getall()
        holder = []
        for item in learn:
            if re.search('^<(p|o|u)', item):
                holder.append(item)
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//div[@data-label='Column'][contains(*/*/text(), 'Career "
                                "outlook')]/following-sibling::*/*/*").getall()
        holder = []
        for item in career:
            if re.search('^<(p|o|u)', item):
                holder.append(item)
        if holder:
            course_item['careerPathways'] = strip_tags(re.sub('<sup>.*?</sup>', '', ''.join(holder), re.DOTALL),
                                                       remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//h2[@class='h3'][contains(text(), 'Entry requirements')]/following-sibling::*").getall()
        holder = []
        for item in entry:
            if re.search('^<(p|o|u|f)', item):
                holder.append(item)
        if holder:
            course_item['entryRequirements'] = strip_tags(''.join(holder), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        duration = response.xpath("//*[text()='Duration']/following-sibling::*").get()
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
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        cost_per_subj = response.xpath("//*[contains(text(), 'Cost per subject')]/following-sibling::*/text()").get()
        if cost_per_subj:
            cost_per_subj = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", cost_per_subj, re.M)
            cost_per_subj = [float(''.join(x)) for x in cost_per_subj]
            if cost_per_subj:
                cost_per_subj = max(cost_per_subj)
        total_subj = response.xpath("//*[contains(text(), 'Total subjects')]/following-sibling::*/text()").get()
        if total_subj:
            total_subj = re.findall('\d+', total_subj)
            total_subj = [float(x) for x in total_subj]
            if total_subj:
                total_subj = max(total_subj)
        if cost_per_subj and total_subj:
            course_item["domesticFeeTotal"] = cost_per_subj * total_subj

        intake = response.xpath("//div[contains(@class, 'tux-c-accordion__heading')][contains(*/text(), 'application "
                                "deadline')]/following-sibling::*").get()
        if intake:
            holder = []
            for item in self.months:
                if re.search(item, intake, re.I | re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        if re.search('online mba', course_name, re.I):
            name = 'Online MBA'
            course_item.set_course_name(name.strip(), self.uidPrefix)

        course_item['modeOfStudy'] = 'Online'

        yield course_item
