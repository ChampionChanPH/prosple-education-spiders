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


class NioSpiderSpider(scrapy.Spider):
    name = 'nio_spider'
    start_urls = ['https://www.nioda.org.au/academic-programs/master-of-leadership-and-management-organisation'
                  '-dynamics/']
    institution = "The National Institute of Organisation Dynamics Australia (NIODA)"
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
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath(
            "//*[@class='et_pb_text_inner']/h2/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath(
            "//*[@class='et_pb_text_inner']/h2/following-sibling::*").get()
        if summary:
            course_item.set_summary(summary.strip())

        overview = response.xpath(
            "//h2[text()='Course Overview']/following-sibling::*").getall()
        if overview:
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//h2[text()='Admission Requirements']/following-sibling::*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath(
            "//h2[text()='Course Content']/following-sibling::*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(
                ''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//h2[text()='Course Structure']/following-sibling::*").getall()
        if structure:
            course_item['courseStructure'] = strip_tags(''.join(structure), remove_all_tags=False,
                                                        remove_hyperlinks=True)

        apply = response.xpath(
            "//h2[text()='How to Apply']/following-sibling::*").getall()
        if apply:
            course_item['howToApply'] = strip_tags(
                ''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        dom_fee = response.xpath("//div[@class='et_pb_text_inner']/*[contains(text(), 'FEES AND "
                                 "COSTS')]/following-sibling::*").getall()
        if dom_fee:
            dom_fee = ''.join(dom_fee)
            dom_fee = re.findall(
                "\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        location = response.xpath(
            "//*[contains(text(), 'Locations')]/following-sibling::*").get()
        campus_holder = []
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)

        duration = response.xpath(
            "//h2[text()='At a glance']/following-sibling::*").getall()
        if duration:
            duration = "".join(duration)
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

        if duration:
            holder = []
            for month in self.months:
                if re.search(month, duration, re.M):
                    holder.append(self.months[month])
            if holder:
                holder = list(set(holder))
                course_item["startMonths"] = "|".join(sorted(holder))

        if duration:
            course_code = re.findall(
                "([A-Z]{3}.*)<", duration, re.DOTALL | re.M)
            if course_code:
                course_item["courseCode"] = course_code[0]

        if duration:
            study_holder = []
            if re.search("face.to.face", duration, re.M | re.I | re.DOTALL):
                study_holder.append("In Person")
            if re.search("online", duration, re.M | re.I):
                study_holder.append("Online")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        yield course_item
