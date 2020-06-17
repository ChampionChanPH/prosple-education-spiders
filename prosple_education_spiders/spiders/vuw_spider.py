# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *


def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"


class VuwSpiderSpider(scrapy.Spider):
    name = 'vuw_spider'
    # allowed_domains = ['https://www.wgtn.ac.nz/study/programmes-courses/undergraduate']
    start_urls = ['https://www.wgtn.ac.nz/study/programmes-courses/undergraduate', 'https://www.wgtn.ac.nz/study/programmes-courses/postgraduate']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Victoria University of Wellington"
    uidPrefix = "NZ-VUW-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "artist diploma": "5",
        # "foundation certificate": "4"
    }

    custom_lua = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(8))
          local element = splash:select("[title='Display information for domestic students']")
          assert(element:mouse_click())
          assert(splash:wait(8))
          return {
            html = splash:html()
          }
        end
    """

    holder = []

    campuses = {
        "kelburn": "50304",
        "pipitea": "50305",
        "te aro": "50306",
        "auckland": "50307",
        "airamar": "50308",
        "online": "Online",
     }

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.catalog_page, args={'wait': 3})

    def catalog_page(self, response):
        courses = response.css("div.search-result")
        for item in courses:
            course = item.css("h4 a::attr(href)").get()
            name = item.css("h4 a::text").get()
            code = item.css("h5.search-result-subtitle::text").get()
            summary = item.css("div.search-result-body p::text").get()
            duration = item.xpath("//p[preceding-sibling::h5/span/text()='Duration']/text()").get()
            # print(name)
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(
                        course,
                        self.course_parse,
                        endpoint='execute',
                        args={'lua_source': self.custom_lua, 'url': course},
                        meta={'url': course, 'name': name, 'code': code, 'summary': summary, 'duration': duration}
                    )

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta["url"]

        name = response.meta["name"]
        if name:
            name = cleanspace(name)
            course_item.set_course_name(name, self.uidPrefix)

        code = response.meta["code"]
        if code:
            code = cleanspace(code)
            course_item["courseCode"] = code

        summary = response.meta["summary"]
        if summary:
            summary = cleanspace(summary)
            course_item.set_summary(summary)

        course_item.set_sf_dt(self.degrees)

        # Overide canonical group
        course_item["group"] = 2
        course_item["canonicalGroup"] = "GradNewZealand"

        duration = response.meta["duration"]
        if duration:
            duration = cleanspace(duration)
            value = re.findall("[\d\.]+", duration)
            course_item["durationMinFull"] = value[0]
            period = duration.split(" ")[-1]
            period = get_period(period)
            if period == 0:
                course_item.add_flag("teachingPeriod", "Invalid period found: "+duration)
            else:
                course_item["teachingPeriod"] = period

        overview = response.css("tooltipify-content").get()
        if overview:
            overview = re.sub("<.*?>", "", overview)
            course_item["overview"] = overview

        campus = response.xpath("//div[preceding-sibling::h3/text()='Location']//strong/text()").get()
        if campus:
            keys = list(self.campuses.keys())
            match = [x in campus.lower() for x in keys]
            match = [keys[match.index(x)] for x in match if x]
            mode_holder = []
            if match:
                # print(match)
                campusNID = [self.campuses[i] for i in match if i != "online"]
                if campusNID:
                    mode_holder.append("In person")
                    course_item["campusNID"] = "|".join(campusNID)

                if "online" in match:
                    mode_holder.append("Online")
                course_item["modeOfStudy"] = "|".join(mode_holder)

            else:
                course_item.add_flag("campusNID", "No campus matches found: "+campus)
        # if "flag" in course_item:
        yield course_item

