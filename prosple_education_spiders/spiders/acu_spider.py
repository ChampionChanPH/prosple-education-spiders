# -*- coding: utf-8 -*-
# by Christian Anasco

from re import L
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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])


class AcuSpiderSpider(scrapy.Spider):
    name = 'acu_spider'
    allowed_domains = ['www.acu.edu.au', 'acu.edu.au']
    start_urls = [
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Undergraduate',
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Postgraduate',
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Research',
        'https://www.acu.edu.au/study-at-acu/find-a-course/course-search-result?CourseType=Other'
    ]
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    institution = "Australian Catholic University (ACU)"
    uidPrefix = "AU-ACU-"

    campuses = {
        "Sydney": "509",
        "Adelaide": "508",
        "National": "510",
        "Ballarat": "506",
        "North Sydney": "504",
        "Canberra": "505",
        "Strathfield": "503",
        "Melbourne": "501",
        "Brisbane": "502"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "undergraduate certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
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
        yield SplashRequest(response.request.url, callback=self.main_parse, args={'wait': 20})

    def main_parse(self, response):
        courses = response.xpath("//section[contains(@class, 'search-results-scholarships')]//input["
                                 "@type='hidden']/@value").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//div[@id='overview-description']/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//div[contains(@class, 'course-details-intro')]/*/*").getall()
        holder = []
        if entry:
            for item in entry:
                if re.search("^<(p|o|u)", item):
                    holder.append(item)
                else:
                    break
        if holder:
            course_item["entryRequirements"] = strip_tags(
                "".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//*[text()='Careers']/following-sibling::*/*").getall()
        if career:
            career = [x for x in career if strip_tags(x) != ""]
            course_item["careerPathways"] = strip_tags(
                "".join(career), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath(
            "//select[@id='location']/option/text()").getall()
        if location:
            location = "|".join(location)
            campus_holder = []
            for campus in self.campuses:
                if campus == "Sydney":
                    if re.search("(?<!North )Sydney", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        start = response.xpath(
            "//dt[contains(text(), 'Start dates')]/following-sibling::dd").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        atar = response.xpath(
            "//dt[contains(text(), 'ATAR')]/following-sibling::dd").get()
        if atar:
            atar = re.findall('\d*\.?\d+', atar, re.M)
            if atar:
                atar = [float(x) for x in atar]
                course_item['guaranteedEntryScore'] = min(atar)

        study = response.xpath(
            "//dt[contains(text(), 'Study mode')]/following-sibling::dd").get()
        holder = []
        if study:
            if re.search("(attendance|multi|campus|person)", study, re.M | re.I):
                holder.append("In Person")
            if re.search("(online|multi|distance)", study, re.M | re.I):
                holder.append("Online")
        if holder:
            course_item['modeOfStudy'] = "|".join(holder)

        course_code = response.xpath(
            "//dt[contains(text(), 'Course code:')]/following-sibling::dd/text()").get()
        if not course_code:
            course_code = response.xpath(
                "//div[contains(*/*/text(), 'Course code:')]/following-sibling::div//text()").get()
        if course_code:
            if strip_tags(course_code) != '':
                course_item["courseCode"] = course_code.strip()

        duration = response.xpath(
            "//dt[contains(text(), 'Duration')]/following-sibling::dd").get()
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
                        course_item["durationMinFull"] = float(
                            duration_full[0][0])
                        self.get_period(
                            duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(
                            duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              "and", "/"], type_delims=["of", "in", "by"])

        if 'courseName' in ['General English', 'IELTS Test Preparation', 'English for the Workplace',
                            'English for Academic Purposes (20 weeks)', 'English for Academic Purposes (10 weeks)']:
            if 'durationMinFull' in course_item:
                course_item['uid'] = course_item['uid'] + \
                    '-' + course_item['durationMinFull']

        if "courseName" in course_item:
            if re.search("postgraduate", course_item["courseName"], re.I):
                course_item["courseLevel"] = "Postgraduate"
                course_item["canonicalGroup"] = "PostgradAustralia"
                course_item["group"] = 4

        international = response.xpath(
            "//select[@id='demographic']/option/text()").getall()
        if "International" in international:
            url = course_item["sourceURL"].replace("Domestic", "International")
            yield response.follow(url, callback=self.international_parse, meta={"item": course_item})
        else:
            yield course_item

    def international_parse(self, response):
        course_item = response.meta["item"]

        course_item["internationalApps"] = 1
        course_item["internationalApplyURL"] = response.request.url

        cricos = response.xpath(
            "//dt[contains(text(), 'CRICOS Code')]/following-sibling::dd").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)

        yield course_item
