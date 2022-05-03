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


class ThsSpiderSpider(scrapy.Spider):
    name = 'ths_spider'
    start_urls = ['https://hotelschool.scu.edu.au/courses/']
    institution = "The Hotel School Australia"
    uidPrefix = "AU-THS-"

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
        "Sydney": "83269",
        "Melbourne": "83272",
        "Brisbane": "83273",
        "Hayman Island": "83274"
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
        courses = response.xpath("//a[text()='Course Information']")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//title/text()").get()
        if course_name:
            course_name = re.split(" \| ", course_name, re.DOTALL)[0]
            course_item.set_course_name(
                strip_tags(course_name), self.uidPrefix)

        overview = response.xpath("//*[@class='intro-wrapper']/*").getall()
        holder = []
        for item in overview:
            if re.search("program updates please click", item, re.M) or re.search("<audio", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath(
            "//*[@class='ico-time']/following-sibling::node()").get()
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

        intake = response.xpath(
            "//*[@class='ico-calendar']/following-sibling::node()").getall()
        if intake:
            intake = "".join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        location = response.xpath(
            "//*[@class='ico-campus']/following-sibling::node()").getall()
        online = response.xpath(
            "//*[@class='ico-course-online']/following-sibling::node()").get()
        campus_holder = set()
        study_holder = set()
        if location:
            location = "".join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.M | re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add("In Person")
        if online:
            study_holder.add("Online")
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        cricos = response.xpath(
            "//*[@class='ico-cricos']/following-sibling::node()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1

        apply_domestic = response.xpath(
            "//*[text()='Domestic Students']/following-sibling::*/"
            "*[text()='Application Process']/following-sibling::*[1]").get()
        apply_international = response.xpath(
            "//*[text()='International Students']/following-sibling::*/"
            "*[text()='Application Process']/following-sibling::*[1]").get()
        holder = []
        if apply_domestic:
            holder.append("<p><strong>Domestic Students</strong></p>")
            holder.append(strip_tags(apply_domestic,
                          remove_all_tags=False, remove_hyperlinks=True))
        if apply_international:
            holder.append("<p><strong>International Students</strong></p>")
            holder.append(strip_tags(apply_international,
                          remove_all_tags=False, remove_hyperlinks=True))
        if holder:
            course_item["howToApply"] = "".join(holder)

        entry_domestic = response.xpath(
            "//*[text()='Domestic Students']/following-sibling::*/"
            "*[text()='Admission Requirements']/following-sibling::*[1]").get()
        entry_international = response.xpath(
            "//*[text()='International Students']/following-sibling::*/"
            "*[text()='Admission Requirements']/following-sibling::*[1]").get()
        holder = []
        if entry_domestic:
            holder.append("<p><strong>Domestic Students</strong></p>")
            holder.append(strip_tags(entry_domestic,
                          remove_all_tags=False, remove_hyperlinks=True))
        if entry_international:
            holder.append("<p><strong>International Students</strong></p>")
            holder.append(strip_tags(entry_international,
                          remove_all_tags=False, remove_hyperlinks=True))
        if holder:
            course_item["entryRequirements"] = "".join(holder)

        career = response.xpath("//*[@class='m-outcomes-intro']/*").getall()
        holder = []
        for item in career:
            if re.search("inline-link", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by', 'for'])

        yield course_item
