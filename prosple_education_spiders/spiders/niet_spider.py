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


class NietSpiderSpider(scrapy.Spider):
    name = 'niet_spider'
    start_urls = ['https://www.niet.edu.au/course/']
    banned_urls = []
    institution = 'National Institute of Education and Technology (NIET)'
    uidPrefix = 'AU-NIET-'

    campuses = {
        "EMP": "119903",
        "HBT": "119904",
    }

    degrees = {
        "graduate certificate": "7",
        "postgraduate certificate": "7",
        "online graduate certificate": "7",
        "graduate diploma": "8",
        "postgraduate diploma": "8",
        "master": research_coursework,
        "mba": research_coursework,
        "online mba": research_coursework,
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
        courses = response.xpath("//a[text()='View Details']/@href").getall()
        yield from response.follow_all(courses, callback=self.course_parse)

        next_page = response.xpath("//a[contains(@class, 'next')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

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

        overview = response.xpath(
            "//*[strong/text()='About this Course:']/following-sibling::*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath(
            "//*[contains(strong/text(), 'll Learn')]/following-sibling::*").getall()
        if learn:
            course_item["whatLearn"] = strip_tags(
                ''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//*[text()='ENTRY REQUIREMENTS']/following-sibling::*//div[@class='left']/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//*[text()='Career Outcomes']/following-sibling::*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        start = response.xpath(
            "//h5[text()='INTAKES']/following-sibling::*/text()").get()
        holder = []
        if start:
            for month in self.months:
                if re.search(month, start, re.M):
                    holder.append(self.months[month])
            if re.search("monthly", start, re.I):
                holder.extend(["01", "02", "03", "04", "05", "06",
                              "07", "08", "09", "10", "11", "12"])
            if holder:
                holder = set(holder)
                course_item["startMonths"] = "|".join(holder.sort())

        study = response.xpath(
            "//h5[text()='STUDY MODE']/following-sibling::*/text()").get()
        holder = []
        if study:
            if re.search("campus", study, re.I | re.M):
                holder.append("In Person")
            if re.search("online", study, re.I | re.M):
                holder.append("Online")
        if holder:
            course_item["modeOfStudy"] = "|".join(holder)

        location = response.xpath(
            "//h5[text()='CAMPUSES']/following-sibling::*/text()").get()
        campus_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        dom_fee = response.xpath(
            "//h5[text()='DOMESTIC FEES']/following-sibling::*/text()").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        code = response.xpath(
            "//h5[text()='COURSE / CRICOS CODES']/following-sibling::*/text()").get()
        if code:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", code, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url
            course_code = re.findall("[A-Z]{3}\d+", code, re.M)
            if course_code:
                course_item["courseCode"] = ", ".join(course_code)

        duration = response.xpath(
            "//h5[text()='DURATION']/following-sibling::*/text()").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
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

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
