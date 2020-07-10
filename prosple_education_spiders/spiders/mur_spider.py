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


class MurSpiderSpider(scrapy.Spider):
    name = 'mur_spider'
    allowed_domains = ['search.murdoch.edu.au', 'murdoch.edu.au']
    start_urls = ['https://search.murdoch.edu.au/s/search.html?collection=mu-course-search']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    banned_urls = []
    courses = []
    institution = "Murdoch University"
    uidPrefix = "AU-MUR-"

    campuses = {
        "Rockingham": "683",
        "Perth": "680",
        "External": "681",
        "Mandurah": "682"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "research masters with training": "12",
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
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
        yield SplashRequest(response.request.url, callback=self.sub_parse, args={'wait': 20})

    def sub_parse(self, response):
        courses = response.xpath("//li[@class='search-tier']/following-sibling::*//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//a[@rel='next']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.sub_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h3[contains(@class, 'h--regular')]/text()").get()
        if course_name.strip() == '' or re.search("fieldname", course_name):
            course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        uid = re.findall("(?<=course-details/).*", course_item["sourceURL"], re.DOTALL)
        if uid:
            course_item["uid"] = self.uidPrefix + uid[0]

        overview = response.xpath("//*[text()='Course Description']/following-sibling::*").getall()
        holder = []
        for item in overview:
            if (not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M)) or \
                    re.search("class=", item, re.M):
                if not re.search("About this course", item, re.M):
                    break
            elif strip_tags(item).strip() != '':
                holder.append(item)
        if len(holder) == 1:
            course_item.set_summary(strip_tags(holder[0]))
            course_item["overview"] = strip_tags("".join(holder), False)
        if len(holder) > 1:
            course_item.set_summary(strip_tags(holder[0] + holder[1]))
            course_item["overview"] = strip_tags("".join(holder), False)

        career = response.xpath(
            "//*[contains(text(), 'Your') and contains(text(), 'career')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if (not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M)) or \
                    re.search("class=", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags("".join(holder), False)

        learn = response.xpath(
            "//*[contains(text(), 'What you') and contains(text(), 'll learn')]/following-sibling::*").getall()
        if not learn:
            learn = response.xpath("//*[text()='Develop your skills']/following-sibling::*").getall()
        holder = []
        for item in learn:
            if (not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M)) or \
                    re.search("class=", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["whatLearn"] = strip_tags("".join(holder), False)

        course_code = response.xpath("//h4[contains(text(), 'Course Code')]/following-sibling::*").get()
        if course_code:
            course_code = re.findall("[0-9A-Z]+", course_code, re.M)
            if course_code:
                course_item["courseCode"] = ", ".join(course_code)

        cricos = response.xpath("//h4[contains(text(), 'CRICOS Code')]/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        score = response.xpath("//h4[contains(text(), 'Selection Rank')]/following-sibling::*").get()
        if score:
            score = re.findall("\d+", score, re.M)
            if score:
                course_item["minScoreNextIntake"] = score[0]

        location = response.xpath("//h4[contains(text(), 'Location')]/following-sibling::*").get()
        if location:
            campus_holder = []
            study_holder = set()
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)
                study_holder.add("In Person")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        duration = response.xpath("//h4[contains(text(), 'Course Duration')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
                                       duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/", "\+"], type_delims=["of", "in", "by"])

        yield course_item