# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import Course
from ..misc_functions import *
from datetime import date
from time import strptime
from scrapy_splash import SplashRequest


class TiwaSpiderSpider(scrapy.Spider):
    name = 'tiwa_spider'
    # allowed_domains = ['https://www.tafeinternational.wa.edu.au/your-study-options/study-at-tafe/course-catalogue']
    start_urls = [
        'https://www.tafeinternational.wa.edu.au/your-study-options/study-at-tafe/course-catalogue/'
    ]

    campus_map = {
        "Albany": "38027",
        "Balga": "38029",
        "Bentley": "38030",
        "Bunbury": "38031",
        "Carlisle": "38032",
        "East Perth": "38033",
        "Fremantle": "38034",
        "Geraldton": "38035",
        "Jandakot": "38036",
        "Joondalup (Kendrew Crescent)": "38038",
        "Kwinana": "38039",
        "Leederville": "38040",
        "Margaret River": "38041",
        "Mt Lawley": "38042",
        "Munster": "38043",
        "Murdoch": "38044",
        "Perth": "38045",
        "Rockingham": "38046",
        "Thornlie": "38047"
    }

    course_data_map = {
        "Duration:": "durationMinFull",
        "Tuition fee:": "feesRaw",
        "Resource fee:": "feesRaw",
        "Materials fee:": "feesRaw"

    }

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    def parse(self, response):
        categories = response.css("div#MSOZoneCell_WebPartWPQ4 a::attr(href)").extract()
        # print(len(courses))
        for category in categories:
            # print(category)
            yield response.follow(category, callback=self.courses)
            # yield SplashRequest(response.urljoin(category), callback=self.course_parse)

    def courses(self, response):
        courses = response.css("a.view-course-btn::attr(href)").extract()
        # print(len(courses))
        for course in courses:
            yield SplashRequest(response.urljoin(course), callback=self.course_parse, args={'wait': 25.0}, meta={'url': response.urljoin(course)})

    def course_parse(self, response):
        canonical_group = "StudyPerth"
        group_number = 23
        institution = "TAFE International Western Australia"
        uidPrefix = "AU-TIWA-"

        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["group"] = group_number
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["canonicalGroup"] = canonical_group
        course_item["internationalApplyURL"] = response.meta['url']
        course_item["domesticApplyURL"] = response.meta['url']

        raw_course_name = response.css("#main h1::text").extract_first()
        if len(re.findall("\d",raw_course_name.split(" ")[0])) > 0:
            course_item["courseName"] = re.sub(raw_course_name.split(" ")[0]+" ","",raw_course_name)
            # course_item["courseCode"] = raw_course_name.split(" ")[0]

        else:
            course_item["courseName"] = raw_course_name

        course_item["uid"] = uidPrefix + course_item["courseName"]

        course_item.set_raw_sf()

        codes = response.css("hgroup h3::text").extract_first()
        # print(codes)
        if codes:
            try:
                course_item["courseCode"] = re.findall("National code: (.*?)\s",codes)[0]
                course_item["cricosCode"] = re.findall("CRICOS code: ([\w\d]*)",codes)[0]

            except IndexError:
                print("Missing code")

        overview = response.css("article.first p::text").extract()
        if len(overview) > 0:
            course_item["overviewSummary"] = overview[0]
            course_item["overview"] = "\n".join(overview)

        course_item["entryRequirements"] = response.css("ul#admission-req").extract_first()
        course_item["careerPathways"] = response.css('div#ctl00_PlaceHolderMain_ctl00_CourseOutline_CourseCareerOpportunities_CareerOpportunities ul').extract_first()

        campuses = unique_list(response.css('span[data-bind*="text: Campus.Location()"]::text').extract())
        campuses = campus_NID(self.campus_map, campuses)
        course_item["campusNID"] = "|".join(campuses)


        course_data = response.css("table.course-data tr")
        course_item["feesRaw"] = []
        for row in course_data:
            row_td = row.css("td").extract_first()
            if row.css("th span::text").extract_first() == "Duration:":
                duration_raw = re.findall("-->(.*?)<!",row_td)[0].split(" ")
                course_item["durationMinFull"] = float(duration_raw[0])
                course_item["teachingPeriod"] = get_period(duration_raw[1])

                intakes = cleanspace(row.css("#SelectedIntakes::text").extract_first())
                intakes = intakes.strip("()").split(" ")
                intakes = convert_months(intakes)
                course_item["startMonths"] = "|".join(intakes)

            elif "tuition fee" in row.css("th span::text").extract_first().lower():
                value = re.sub(",","",re.findall("\$([\d,]+)",row_td)[0])
                period = re.findall("per\s(\w+)",row_td)
                multiplier = re.findall("\((\d+)\s\w+\)",row_td)

                if period:
                    multiplier = int(multiplier[0])
                    if period[0] == "semester" and multiplier > 1:
                        course_item["internationalFeeAnnual"] = int(value) * 2
                    course_item["internationalFeeTotal"] = int(value) * multiplier

        yield course_item




                # course_item["feesRaw"].append(row.css("td::text").extract_first())
            # print(row.css("th span::text").extract_first())
        # print(course_data)

        # print(response.css('section#course-institute-info').extract_first())
        # print(response.css('#SelectedPeriodId+ span::text').extract_first())
        # print(response.css('span[data-bind*="text: Institute.OrganisationName"]::text').extract_first())