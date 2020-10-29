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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


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
        yield SplashRequest(response.request.url, callback=self.main_parse, args={'wait': 15})

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

        overview = response.xpath("//div[@id='course--description--domestic']/*[contains(*/text(), "
                                  "'Description')]/following-sibling::*[1]/*").getall()
        if not overview:
            overview = response.xpath("//h2[contains(text(), 'Key features of the course')]/preceding-sibling::*").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            holder = []
            for item in overview:
                if not re.search("^<p", item) and not re.search("^<div", item) and not re.search("^<ul", item):
                    break
                else:
                    holder.append(item)
            if holder:
                course_item["overview"] = strip_tags("".join(holder), False)

        entry = response.xpath("//div[@id='course--requirements--domestic']/*[contains(*/text(), "
                               "'Essential requirements for admission')]/following-sibling::*[1]/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags("".join(entry), False)

        career = response.xpath("//div[@id='course--career--domestic']/*[contains(*/text(), "
                                "'Career paths')]/following-sibling::*[1]/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags("".join(career), False)

        location = response.xpath("//dt[contains(text(), 'Location:')]/following-sibling::dd").get()
        if not location:
            location = response.xpath("//div[contains(*/*/text(), 'Location:')]/following-sibling::div").get()
        if location:
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        start = response.xpath("//dt[contains(text(), 'Intakes:')]/following-sibling::dd").get()
        if not start:
            start = response.xpath("//div[contains(*/*/text(), 'Intakes:')]/following-sibling::div").get()
        if start:
            start_holder = []
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        cricos = response.xpath("//dt[contains(text(), 'CRICOS:')]/following-sibling::dd").get()
        if not cricos:
            cricos = response.xpath("//div[contains(*/*/text(), 'CRICOS:')]/following-sibling::div").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        atar = response.xpath("//dt[contains(text(), 'ATAR')]/following-sibling::dd").get()
        if atar:
            atar = re.findall('\((\d{2}\.\d{2})\)', atar, re.M)
            atar = [float(x) for x in atar]
            course_item['guaranteedEntryScore'] = min(atar)

        course_code = response.xpath("//dt[contains(text(), 'Course code:')]/following-sibling::dd").get()
        if not course_code:
            course_code = response.xpath("//div[contains(*/*/text(), 'Course code:')]/following-sibling::div").get()
        if course_code:
            course_code = re.findall("[0-9a-zA-Z]+?", course_code, re.M)
            if course_code:
                course_item["courseCode"] = ", ".join(course_code)

        duration = response.xpath("//dt[contains(text(), 'Duration:')]/following-sibling::dd").get()
        if not duration:
            duration = response.xpath("//div[contains(*/*/text(), 'Duration:')]/following-sibling::div").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration,
                                       re.I | re.M | re.DOTALL)
            if duration_full:
                if len(duration_full) == 1:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full) == 2:
                    duration_full.sort()
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    course_item["durationMaxFull"] = float(duration_full[1][0])
                    self.get_period(duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        if "courseName" in course_item:
            if re.search("postgraduate", course_item["courseName"], re.I):
                course_item["courseLevel"] = "Postgraduate"
                course_item["canonicalGroup"] = "PostgradAustralia"
                course_item["group"] = 4

        yield course_item
