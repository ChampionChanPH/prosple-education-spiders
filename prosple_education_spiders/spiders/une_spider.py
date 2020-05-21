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


class UneSpiderSpider(scrapy.Spider):
    name = 'une_spider'
    allowed_domains = ['my.une.edu.au', 'une.edu.au']
    start_urls = ['http://my.une.edu.au/courses/2020/courses/browse/']
    banned_urls = ['https://my.une.edu.au/courses/2020/courses/GDPSYA',
                   'https://my.une.edu.au/courses/2020/courses/MHMI']
    institution = "University of New England (UNE)"
    uidPrefix = "AU-UNE-"
    campuses = {
        "Sydney": "765",
        "Armidale": "764"
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//div[@class='content']//td/a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//div[@class='content']//h2/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@id='overviewTab-leftColumn']//*[preceding-sibling::h4][following-sibling::h4]").getall()
        if len(overview) == 0:
            overview = response.xpath("//div[@id='overviewTab-leftColumn']//*[preceding-sibling::h4]["
                                      "following-sibling::*[contains(text(), 'Need assistance')]]").getall()
        if len(overview) > 0:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, False)

        summary = response.xpath("//div[@id='overviewTab-leftColumn']//h4/following-sibling::p[1]//text()").getall()
        if len(summary) > 0:
            summary = " ".join([x.strip() for x in summary])
            summary = re.split("(?<=[\.\?])\s", summary)
            if len(summary) == 1:
                course_item["overviewSummary"] = summary[0]
            if len(summary) >= 2:
                course_item["overviewSummary"] = summary[0] + " " + summary[1]

        career = response.xpath("//div[@id='overviewTab-leftColumn']//*[preceding-sibling::*[contains(text(), "
                                "'Career Opportunities')]][following-sibling::*[contains(text(), "
                                "'Need assistance')]]").getall()
        if len(career) > 0:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(career, remove_all_tags=False)

        table_holder = []
        for title, description in zip(response.xpath("//table[@id='furtherInformationTable']/tr/td[1]").getall(),
                                      response.xpath("//table[@id='furtherInformationTable']/tr/td[2]").getall()):
            title = re.sub("</?td>", "", title)
            description = re.sub("</?td>", "", description)
            holder = [title.strip(), description.strip()]
            table_holder.append(holder)

        for row in table_holder:
            if re.search("abbreviation", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["courseCode"] = row[1]
            if re.search("cricos", row[0], re.IGNORECASE | re.MULTILINE):
                cricos = re.findall("\d{6}[0-9a-zA-Z]", row[1], re.M)
                if len(cricos) > 0:
                    course_item["cricosCode"] = ", ".join(cricos)
                    course_item["internationalApps"] = 1
                    course_item["internationalApplyURL"] = response.request.url
            if re.search("commencing", row[0], re.IGNORECASE | re.MULTILINE):
                study_holder = []
                campus_holder = []
                if re.search("campus", row[1], re.IGNORECASE | re.MULTILINE):
                    study_holder.append("In Person")
                if re.search("online", row[1], re.IGNORECASE | re.MULTILINE):
                    study_holder.append("Online")
                course_item["modeOfStudy"] = "|".join(study_holder)
                for campus in self.campuses:
                    if re.search(campus, row[1], re.IGNORECASE | re.MULTILINE):
                        campus_holder.append(self.campuses[campus])
                course_item["campusNID"] = "|".join(campus_holder)
            if re.search("duration", row[0], re.IGNORECASE | re.MULTILINE):
                if re.search("\sor\s", row[1], re.M):
                    duration_full = re.findall("(\d*\.?\d+)\sor\s(\d*\.?\d+)(?=\s("
                                               "year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                               row[1], re.I | re.M)
                else:
                    duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s"
                                               "?\sfull.time)", row[1], re.I | re.M)
                duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart"
                                           ".time)", row[1], re.I | re.M)
                if len(duration_full) == 0 and len(duration_part) > 0:
                    self.get_period(duration_part[0][1].lower(), course_item)
                if len(duration_full) > 0:
                    if len(duration_full[0]) == 2:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full[0]) == 3:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                        self.get_period(duration_full[0][2].lower(), course_item)
                if len(duration_part) > 0:
                    if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                        course_item["durationMinPart"] = float(duration_part[0][0])
                    else:
                        course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                         / self.teaching_periods[duration_part[0][1].lower()]

            if re.search("Guaranteed ATAR", row[0], re.I | re.M):
                course_item["guaranteedEntryScore"] = row[1]
            if re.search("Entry Requirements", row[0], re.I | re.M):
                course_item["entryRequirements"] = strip_tags(row[1], False)
            if re.search("How to Apply", row[0], re.I | re.M):
                course_item["howToApply"] = strip_tags(row[1], False)

        table_holder = []
        for title, description in zip(response.xpath("//table[@id='courseOutcomesTable']/tr/td[1]").getall(),
                                      response.xpath("//table[@id='courseOutcomesTable']/tr/td[2]").getall()):
            title = re.sub("</?td>", "", title)
            description = re.sub("</?td>", "", description)
            holder = [title.strip(), description.strip()]
            table_holder.append(holder)

        for row in table_holder:
            if re.search(r"Course Aims", row[0], re.I | re.M):
                course_item["overviewSummary"] = strip_tags(row[1])
            if re.search("learning", row[0], re.I | re.M):
                course_item["whatLearn"] = strip_tags(row[1], False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        if re.search("This course is not offered in 2020", course_item["overview"], re.M | re.I) or \
                re.search("Exit Award", course_item["overview"], re.M | re.I) or \
                re.search("Applications for 2020 Open Soon", course_item["overview"], re.M | re.I) or \
                response.request.url in self.banned_urls:
            return

        yield course_item