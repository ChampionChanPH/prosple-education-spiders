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
                course_item[field_to_update] = float(course_item[field_to_use]) *\
                    float(course_item["durationMinFull"]) / 12
        if course_item["teachingPeriod"] == 52:
            if float(course_item["durationMinFull"]) < 52:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) *\
                    float(course_item["durationMinFull"]) / 52


class GaSpiderSpider(scrapy.Spider):
    name = 'ga_spider'
    start_urls = [
        'https://generalassemb.ly/browse/courses-and-classes?eveningOneWeek=true&immersive=true']
    institution = "General Assembly"
    uidPrefix = "AU-NIO-"
    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Melbourne": "43679",
        "Sydney": "45896"
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
        courses = response.xpath(
            "//div[contains(@class, 'css-1gz9vyw')]")

        for item in courses:
            duration = item.xpath(
                "..//svg[g[contains(@class, 'ClockOutlineIcon_svg')]]/following-sibling::*").get()
            study = item.xpath(
                "..//svg[g[contains(@class, 'LocationMarkerIcon_svg')]]/following-sibling::*").get()
            yield response.follow(item, callback=self.course_parse, meta={"duration": duration, "study": study})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath(
            "//h1[@class='program__title']/span/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[@class='program__summary']/*").get()
        if overview:
            course_item.set_summary(overview)
            course_item["overview"] = strip_tags(
                overview, remove_all_tags=False, remove_hyperlinks=True)

        overview = response.xpath(
            "//*[contains(@class, 'block__title') and contains(text(), 'relevant today?')]/following-sibling::*/*/*").getall()
        if overview:
            course_item["overview"] = strip_tags(
                "".join(overview), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//*[contains(@class, 'block__title') and contains(text(), 'Are there any prerequisites?')]/following-sibling::*/*/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        study = response.meta["study"]
        holder = []
        if study:
            if re.search("campus", study, re.I | re.M):
                holder.append("In Person")
            if re.search("online", study, re.I | re.M):
                holder.append("Online")
        if holder:
            course_item["entryRequirements"] = "|".join(holder)

        duration = response.meta["duration"]
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?,?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?,?\s+?part)",
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

        learn = response.xpath(
            "//h2[@class='h1-style']/following-sibling::*").getall()
        if learn:
            course_item["whatLearn"] = strip_tags(
                ''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        yield course_item
