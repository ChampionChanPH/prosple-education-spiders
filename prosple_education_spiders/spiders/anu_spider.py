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

class AnuSpiderSpider(scrapy.Spider):
    name = 'anu_spider'
    # allowed_domains = ['https://programsandcourses.anu.edu.au/catalogue']
    start_urls = ['https://programsandcourses.anu.edu.au/catalogue']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "https://programsandcourses.anu.edu.au/2020/program/5050XNAWD"
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "Australian National University (ANU)"
    uidPrefix = "AU-ANU-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "undergraduate certificate": "4",
        "postgraduate diploma": "8",
        "artist diploma": "5",
        "non-award": "13",
        "non award": "13",
        "juris doctor (honours)": "10",
        "flexible double masters": "11",
        "flexible double degree": "2",
        "executive master": "11",
        "graduate non-award": "8",  # assigning a graduate type to get right course level then just assign non-award override after
        # "foundation certificate": "4"
    }

    custom_lua = """
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(3))
      local element = splash:select('a[data-template="program-template"]')
      assert(element:mouse_click())
      assert(splash:wait(3))
      return {
        html = splash:html(),
        png = splash:png(),
        har = splash:har(),
      }
    end
    """
    def parse(self, response):
        yield SplashRequest(
            response.request.url,
            self.course_catalog,
            endpoint='execute',
            args={'lua_source': self.custom_lua, 'url': response.request.url},
            meta={'url': response.request.url}
        )

    def course_catalog(self, response):
        courses = response.css("table.catalogue-search-results__table tbody tr")
        for row in courses:
            cells = row.css("td")
            code = cleanspace(cells[0].css("td a::text").get())
            course = r"https://programsandcourses.anu.edu.au" + cells[0].css("td a::attr(href)").get()
            name = cleanspace(cells[1].css("td a::text").get())
            level = cleanspace(cells[3].css("td::text").get())
            duration = cleanspace(cells[5].css("td::text").get())
            study_mode = cleanspace(cells[6].css("td::text").get())
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(
                        course,
                        callback=self.course_parse,
                        args={'wait': 3},
                        meta={
                            'code': code,
                            'name': name,
                            'level': level,
                            'duration': duration,
                            'study_mode': study_mode,
                            'url': course
                        }
                    )

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta["url"]

        course_item["campusNID"] = "569"

        name = re.sub("<.*?>", "", response.meta['name'])
        if name:
            course_item.set_course_name(name, self.uidPrefix)
        course_item.set_sf_dt(self.degrees, type_delims=["of", "in", "-"])

        # Overrides
        level = response.meta["level"]
        # print([level])
        if level in ["Postgraduate", "Research"]:
            course_item["courseLevel"] = "2"
            if level == "Research":
                course_item["degreeType"] = "12"

        elif level == "Undergraduate":
            course_item["courseLevel"] = "1"

        elif level == "Non-award":
            course_item["degreeType"] = "13"


        code = response.meta["code"]
        if code:
            course_item["courseCode"] = code

        study_mode = response.meta["study_mode"]
        if study_mode:
            if study_mode == "In Person":
                course_item["modeOfStudy"] = "In person"

            elif study_mode == "Online":
                course_item["modeOfStudy"] = "Online"

            elif study_mode == "Multi-Modal":
                course_item["modeOfStudy"] = "In person|Online"

            else:
                course_item.add_flag("modeOfStudy", "New keyword found: " + study_mode)

        overview = response.css("div.introduction p::text").getall()
        if overview:
            overview = [cleanspace(x) for x in overview]
            course_item["overview"] = "\n".join(overview)
            course_item.set_summary(" ".join(overview))

        int_fee = response.css("div#indicative-fees__international dd::text").get()
        if int_fee:
            fee = re.findall("[\d\.,]+", int_fee)
            if fee:
                course_item["internationalFeeTotal"] = fee[0].replace(",", "")

        cricos = response.xpath("//span[preceding-sibling::span/text()='CRICOS code']/text()").get()
        if cricos:
            if cricos != "NO CRICOS":
                course_item["cricosCode"] = cleanspace(cricos)
                course_item["internationalApps"] = 1

        duration = response.meta["duration"]
        if duration:
            duration = float(duration)
            course_item["teachingPeriod"] = 1
            course_item["durationMinFull"] = duration


        # if "flag" in course_item:
        yield course_item

