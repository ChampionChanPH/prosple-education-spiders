# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import Course
from ..misc_functions import *
from datetime import date
from time import strptime
from scrapy_splash import SplashRequest


def research_coursework(course_item):
    if "research" in course_item["sourceURL"]:
        return "12"
    else:
        return "11"


def bachelor_honours(course_item):
    if "honours" in course_item["sourceURL"]:
        return "3"
    else:
        return "2"


def doctor(course_item):
    if course_item["courseLevel"] == "Undergraduate":
        return "2"
    else:
        return "6"


class WsuSpiderSpider(scrapy.Spider):
    name = 'wsu_spider'
    start_urls = ['https://www.westernsydney.edu.au/future/study/courses.html']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    groups = {
                "Postgraduate": {"number": 4, "name": "PostgradAustralia"},
                "Undergraduate": {"number": 3, "name": "The Uni Guide"}
              }
    campus_map = {
        "Bankstown": "39700",
        "Campbelltown": "39701",
        "Hawkesbury": "39702",
        "Lithgow": "39703",
        "Liverpool City": "39704",
        "Nirimba": "39705",
        "Parramatta City": "39707",
        "Parramatta South": "39708",
        "Penrith": "39709",
        "Sydney City": "39710",
        "Sydney Olympic Park": "39711"
    }

    fee_map = {
        "domestic student": ["domesticFeeTotal", "internationalFeeTotal"],
        "international student": ["internationalFeeTotal", "domesticFeeTotal"]
    }

    degrees = {"graduate certificate": {"rank": 2, "level": "Postgraduate", "type": "7"},
               "graduate diploma": {"rank": 2, "level": "Postgraduate", "type": "8"},
               "master": {"rank": 2, "level": "Postgraduate", "type": research_coursework},
               "bachelor": {"rank": 1, "level": "Undergraduate", "type": bachelor_honours},
               "doctor": {"rank": 1, "level": "Undergraduate", "type": doctor},
               "certificate": {"rank": 1, "level": "Undergraduate", "type": "4"},
               "diploma": {"rank": 1, "level": "Undergraduate", "type": "5"},
               "associate degree": {"rank": 1, "level": "Undergraduate", "type": "1"},
               "university foundation studies": {"rank": 1, "level": "Undergraduate", "type": "13"},
               "non-award": {"rank": 1, "level": "Undergraduate", "type": "13"},
               "no match": {"rank": 99, "level": "no match", "type": "15"}
    }

    count = 0
    courses_scraped = []
    blacklist =["http://www.westernsydney.edu.au/future/study/courses/tesol-and-interpreting-and-translation-courses.html"]

    def parse(self, response):
        print(response.request.url)
        yield SplashRequest(response.request.url, callback=self.mainpage_splash, args={'wait': 10}) #need to load js for main page.

    def mainpage_splash(self, response):
        categories = response.css("article.tile__2x2 a::attr(href)").extract()
        for category in categories:
        # print(categories[7])
            if category != "http://www.westernsydney.edu.au/future/why-western.html":
                yield SplashRequest(category, callback=self.category_splash, args={'wait': 10})

    def category_splash(self, response):
        courses = response.css("article.tile__1x1 a::attr(href)").extract()
        courses = list(dict.fromkeys(courses, 0).keys())
        if "#" in courses:
            del courses[courses.index("#")]

        for course in courses:
            if course not in self.courses_scraped and course not in self.blacklist:
                # print(course)
                self.count += 1
                # print(self.count)
                self.courses_scraped.append(course)
                yield SplashRequest(course, callback=self.course_parse, args={'wait': 20}, meta={'url': course})

    def course_parse(self, response):

        institution = "Western Sydney University"
        uidPrefix = "AU-WSU-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["published"] = 1
        course_item["institution"] = institution

        course_item["domesticApplyURL"] = response.meta['url']

        course_item["courseName"] = response.css("h1.title__text::text").extract_first()
        course_item["uid"] = uidPrefix + course_item["courseName"]
        course_level = response.css("div.pb__content-inner span::text").extract_first()
        if course_level in ["Undergraduate", "The College"]:
            course_item["courseLevel"] = "Undergraduate"

        else:
            course_item["courseLevel"] = "Postgraduate"
        course_item["canonicalGroup"] = self.groups[course_item["courseLevel"]]["name"]
        course_item["group"] = self.groups[course_item["courseLevel"]]["number"]

        course_item.set_sf_dt(self.degrees)

        info_block = response.css("div.tile-carousel-side")#get block that has overview, duration and intake
        course_description = info_block[0].css("div.component--wysiwyg p::text").extract()
        course_item["overviewSummary"] = cleanspace(course_description[0])
        course_item["overview"] = "\n".join([cleanspace(x) for x in course_description])

        columns = info_block[0].css("div.col-sm-6")

        for column in columns:
            # print(column.extract())
            header = column.css("div.h3::text").extract_first()
            if header == "Start times":
                months = column.css("span::text").extract()
                months = convert_months(" ".join(months).split(" "))
                course_item["startMonths"] = "|".join(months)

            elif header == "Study options":
                rows = column.css("div.cols-2__body")
                for row in rows:
                    # print(row.extract())
                    cat = row.css("div.h6::text").extract_first()
                    value = row.css("span::text").extract_first()
                    duration = re.findall("[\d.]+",value)[0]
                    period = re.findall("[a-zA-Z]+",value)[0]
                    # print(duration)
                    if "teachingPeriod" in course_item:
                        if get_period(period.lower()) != course_item["teachingPeriod"]:
                            course_item.add_flag("teachingPeriod", "durations have different periods")
                    else:
                        course_item["teachingPeriod"] = get_period(period.lower())

                    if cat == "PART TIME":
                        course_item["durationMinPart"] = duration

                    elif cat == "FULL TIME":
                        course_item["durationMinFull"] = duration

        campus_blocks = response.css("div.col-lg-7 div.tile-carousel__text")
        campuses = campus_blocks.css("h3::text").extract()
        course_item["campusNID"] = "|".join([self.campus_map[x] for x in campuses if x != "Online"])
        if "Online" in campuses:
            if len(campuses) == 1:
                course_item["modeOfStudy"] = "Online"
            else:
                course_item["modeOfStudy"] = "In person|Online"
        else:
            course_item["modeOfStudy"] = "In person"
        for campus_block in campus_blocks:
            codes = campus_block.css("dl")
            for code in codes:
                label = code.css("dt::text").extract_first()
                value = code.css("dd::text").extract_first()
                if label == "COURSE CODE":
                    if "courseCode" in course_item and value != course_item["courseCode"]:
                        course_item.add_flag("courseCode", "Inconsistent course code")
                    else:
                        if re.match("\d+", value):
                            course_item["courseCode"] = value

                elif label == "CRICOS CODE":
                    course_item["internationalApps"] = 1
                    course_item["internationalApplyURL"] = response.meta['url']
                    if "cricosCode" in course_item and value != course_item["cricosCode"]:
                        course_item.add_flag("courseCode", "Inconsistent cricos code")
                    else:
                        course_item["cricosCode"] = value

        rows = response.css("div.section div.row")
        for row in rows:
            title = row.css("h3.title__text::text").extract_first()
            if title:
                title = cleanspace(title)
            if title == "Fees and delivery":
                field_case = self.fee_map[row.css("option[aria-selected='true']::text").extract_first().lower()]
                fees = row.css("div.tabs__pane")
                for i in range(len(fees)):
                    holder = re.findall("\$([\d,]+)", " ".join(fees[i].css("p::text").extract()))
                    if holder:
                        course_item[field_case[i]] = re.sub(",", "", holder[0])

        yield course_item
