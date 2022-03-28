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


class UndSpiderSpider(scrapy.Spider):
    name = 'und_spider'
    allowed_domains = ['www.notredame.edu.au', 'notredame.edu.au']
    start_urls = ['https://www.notredame.edu.au/study/programs']
    banned_urls = ['https://www.notredame.edu.au/programs/fremantle/school-of-arts-and-sciences/undergraduate/double'
                   '-degrees', 'https://www.notredame.edu.au/programs/re-usable-snippets/template']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = 'The University of Notre Dame Australia'
    uidPrefix = "AU-UND-"
    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "undergraduate certificate": "4",
        "certificate iv": "4",
        "certificate iii": "4",
        "certificate ii": "4",
        "certificate i": "4",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Sydney": "778",
        "Fremantle": "777",
        "Broome": "779"
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

    lua = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(2.0))
          local category = splash:select(args.selector_category)
          assert(category:mouse_click())
          assert(splash:wait(2.0))
          return {
            html = splash:html(),
            }
        end
    """

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.splash_index, args={'wait': 5},
                            meta={'url': response.request.url})

    def splash_index(self, response):
        categories = response.css(".course-tiles__item::attr(id)").getall()

        for item in categories:
            selector = "#" + item + " a"
            yield SplashRequest(response.meta["url"], callback=self.program_parse, endpoint='execute',
                                args={'lua_source': self.lua, 'url': response.meta["url"],
                                      'selector_category': selector})

    def program_parse(self, response):
        courses = response.xpath(
            "//ul[@class='program-list']//a[@class='program-list__title']/@href").getall()

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
            course_name = re.sub('^[A-Z]+[0-9]+', '', course_name)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//h1/following-sibling::div").get()
        if overview:
            course_item["overview"] = strip_tags(
                overview, remove_all_tags=False, remove_hyperlinks=True)

        summary = response.xpath(
            "//h1/following-sibling::div[1]/*[2]//text()").getall()
        second = response.xpath(
            "//h1/following-sibling::div[1]/*[3]//text()").getall()
        if summary:
            summary = " ".join([x.strip() for x in summary])
            if second:
                second = " ".join([x.strip() for x in second])
                summary = summary + " " + second
        if summary:
            course_item.set_summary(summary)

        duration = response.xpath(
            "//*[contains(strong/text(), 'Duration')]/following-sibling::*").get()
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

        location = response.xpath(
            "//*[contains(strong/text(), 'Campus')]/following-sibling::*").get()
        campus_holder = []
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)

        study = response.xpath(
            "//*[contains(strong/text(), 'Study mode')]/following-sibling::*").get()
        study_holder = []
        if study:
            if re.search("online", study, re.I | re.M):
                study_holder.append("Online")
            if re.search("on campus", study, re.I | re.M):
                study_holder.append("In Person")
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        code = response.xpath(
            "//*[contains(strong/text(), 'Code')]/following-sibling::*").get()
        if code:
            course_code = re.findall(r"Program Code (\w+)", code, re.M | re.I)
            cricos_code = re.findall(
                r"CRICOS Code (\d{6}[0-9a-zA-Z])", code, re.M | re.I)
            if course_code:
                course_item["courseCode"] = ", ".join(course_code)
            if cricos_code:
                course_item["cricosCode"] = ", ".join(cricos_code)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        for campus in self.campuses:
            if re.search(campus, response.request.url, re.I):
                course_item["uid"] = self.uidPrefix + \
                    re.sub(
                        " ", "-", course_item["courseName"]) + "-" + campus.title()
                if "courseCode" in course_item:
                    course_item["uid"] = course_item["uid"] + \
                        "-" + course_item["courseCode"]

        entry = response.xpath(
            "//*[contains(text(), 'Entry requirements')]/following-sibling::*").getall()
        if not entry:
            entry = response.xpath(
                "//*[contains(text(), 'Admission requirements')]/following-sibling::*").getall()
        if entry:
            entry = "".join(entry)
            course_item["entryRequirements"] = strip_tags(
                entry, remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath(
            "//*[contains(text(), 'Why study this')]/following-sibling::*").getall()
        if not learn:
            learn = response.xpath(
                "//*[contains(text(), 'About this')]/following-sibling::*").getall()
        if learn:
            learn = "".join(learn)
            course_item["whatLearn"] = strip_tags(
                learn, remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//*[contains(text(), 'Program summary')]/following-sibling::*").getall()
        if not structure:
            structure = response.xpath(
                "//*[contains(text(), 'Program structure')]/following-sibling::*").getall()
        if not structure:
            structure = response.xpath(
                "//*[contains(text(), 'Program outline')]/following-sibling::*").getall()
        if structure:
            structure = "".join(structure)
            course_item["courseStructure"] = strip_tags(
                structure, remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//*[contains(text(), 'Career opportunities')]/following-sibling::*").getall()
        if career:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(
                career, remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        if response.request.url not in self.banned_urls:
            yield course_item
