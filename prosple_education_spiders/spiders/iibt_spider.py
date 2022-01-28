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


class IibtSpiderSpider(scrapy.Spider):
    name = 'iibt_spider'
    start_urls = ['http://www.iibt.edu.au/course-all/']
    institution = "International Institute of Business and Technology (IIBT)"
    uidPrefix = "AU-IIBT-"

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
        "Perth Campus": "83028",
        "Sydney Campus": "83029",
        "Brisbane Campus": "83027"
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
        courses = response.xpath("//*[@class='rtin-title']/a")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.xpath("//*[@class='entry-title']/text()").get()
        if name:
            if re.search("[A-Z0-9]+[A-Z0-9]+ ", name):
                course_code, course_name = re.split("\\s", name, maxsplit=1)
                course_item.set_course_name(strip_tags(course_name), self.uidPrefix)
                course_item["courseCode"] = course_code
            else:
                course_item.set_course_name(strip_tags(name), self.uidPrefix)

        overview = response.xpath("//*[@class='entry-content']/*").getall()
        holder = []
        if overview:
            for item in overview[1:]:
                if re.search("^<style", item):
                    break
                else:
                    holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath("//strong[contains(text(), 'Course Structure')]/following-sibling::node()").getall()
        holder = []
        for item in structure:
            if re.search("^<strong", item):
                break
            elif not re.search("^<br", item):
                holder.append(item)
        if holder:
            course_item["courseStructure"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        entry_tab = response.xpath("//li[@role='presentation']/a[*/text()='Entry Requirements']/@aria-controls").get()
        if entry_tab:
            entry_xpath = "//*[@id='" + entry_tab + "']/*"
            entry = response.xpath(entry_xpath).getall()
            if entry:
                course_item["entryRequirements"] = strip_tags("".join(entry), remove_all_tags=False,
                                                              remove_hyperlinks=True)

        career_tab = response.xpath("//li[@role='presentation']/a[*/text()='Job Roles']/@aria-controls").get()
        if career_tab:
            career_xpath = "//*[@id='" + career_tab + "']/*"
            career = response.xpath(career_xpath).getall()
            if career:
                course_item["careerPathways"] = strip_tags("".join(career), remove_all_tags=False,
                                                           remove_hyperlinks=True)

        intake_tab = response.xpath("//li[@role='presentation']/a[*/text()='Intake Dates']/@aria-controls").get()
        intake = None
        if intake_tab:
            intake_xpath = "//*[@id='" + intake_tab + "']/*"
            intake = response.xpath(intake_xpath).getall()
        if not intake:
            intake = response.xpath("//strong[contains(text(), 'Intake Dates')]/following-sibling::node()").getall()
            holder = []
            for item in intake:
                if re.search("^<strong", item):
                    break
                elif not re.search("^<br", item):
                    holder.append(item)
            if holder:
                intake = holder[:]
        if intake:
            intake = "".join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        study = response.xpath("//strong[contains(text(), 'Mode of Delivery')]/following-sibling::node()").getall()
        holder = []
        for item in study:
            if re.search("^<strong", item):
                break
            elif not re.search("^<br", item):
                holder.append(item)
        if holder:
            study = "".join(holder)
            study_holder = set()
            if re.search("face", study, re.I | re.M):
                study_holder.add("In Person")
            if re.search("online", study, re.I | re.M):
                study_holder.add("Online")
            if study_holder:
                course_item['modeOfStudy'] = '|'.join(study_holder)

        duration = response.xpath("//strong[contains(text(), 'Duration')]/following-sibling::node()").getall()
        holder = []
        for item in duration:
            if re.search("^<strong", item):
                break
            elif not re.search("^<br", item):
                holder.append(item)
        if holder:
            duration = "".join(holder)
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

        course_item["campusNID"] = "83027|83028|83029"

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        yield course_item
