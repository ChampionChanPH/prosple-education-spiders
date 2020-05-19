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


class UndSpiderSpider(scrapy.Spider):
    name = 'und_spider'
    allowed_domains = ['www.notredame.edu.au', 'notredame.edu.au']
    start_urls = ['https://www.notredame.edu.au/study/programs']
    banned_urls = ['https://www.notredame.edu.au/programs/fremantle/school-of-arts-and-sciences/undergraduate/double'
                   '-degrees']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "University of Notre Dame Australia"
    uidPrefix = "AU-UND-"

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
        courses = response.xpath("//ul[@class='program-list']//a[@class='program-list__title']/@href").getall()

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
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[contains(text(), 'Why study this degree')]/following-sibling::*").getall()
        if len(overview) > 0:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, remove_all_tags=False)

        summary = response.xpath("//h1/following-sibling::*/*[2]").get()
        if summary is not None:
            course_item["overviewSummary"] = strip_tags(summary, remove_all_tags=True)

        duration = response.xpath("//*[contains(strong/text(), 'Duration')]/following-sibling::*").get()
        if duration is not None:
            duration = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration, re.M)
        if duration is not None:
            if len(duration) == 1:
                course_item["durationMinFull"] = float(duration[0][0])
                self.get_period(duration[0][1], course_item)
            elif len(duration) == 2:
                course_item["durationMinFull"] = float(duration[0][0])
                course_item["durationMaxFull"] = float(duration[1][0])
                self.get_period(duration[1][1], course_item)

        location = response.xpath("//*[contains(strong/text(), 'Campus')]/following-sibling::*").get()
        campus_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)

        study = response.xpath("//*[contains(strong/text(), 'Study mode')]/following-sibling::*").get()
        study_holder = []
        if study is not None:
            if re.search("online", study, re.I | re.M):
                study_holder.append("Online")
            if re.search("on campus", study, re.I | re.M):
                study_holder.append("In Person")
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)

        code = response.xpath("//*[contains(strong/text(), 'Code')]/following-sibling::*").get()
        if code is not None:
            course_code = re.findall(r"Program Code (\w+)", code, re.M | re.I)
            cricos_code = re.findall(r"CRICOS Code (\d{6}[0-9a-zA-Z])", code, re.M | re.I)
            if len(course_code) > 0:
                course_item["courseCode"] = str(", ".join(course_code))
            if len(cricos_code) > 0:
                course_item["cricosCode"] = str(", ".join(cricos_code))
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        entry = response.xpath("//*[contains(text(), 'Entry requirements')]/following-sibling::*").getall()
        if len(entry) > 0:
            entry = "".join(entry)
            course_item["entryRequirements"] = strip_tags(entry, remove_all_tags=False)

        structure = response.xpath("//*[contains(text(), 'Program summary')]/following-sibling::*").getall()
        if len(structure) > 0:
            structure = "".join(structure)
            course_item["courseStructure"] = strip_tags(structure, remove_all_tags=False)

        career = response.xpath("//*[contains(text(), 'Career opportunities')]/following-sibling::*").getall()
        if len(career) > 0:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(career, remove_all_tags=False)

        course_item.set_sf_dt(self.degrees)

        if response.request.url not in self.banned_urls:
            yield course_item
