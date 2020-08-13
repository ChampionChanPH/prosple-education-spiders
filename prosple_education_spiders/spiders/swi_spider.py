# -*- coding: utf-8 -*-
# by Christian Anasco
# remove courses with "201X only" on course name - 2017, 2018 or 2019

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
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class SwiSpiderSpider(scrapy.Spider):
    name = 'swi_spider'
    start_urls = ['https://www.swinburne.edu.au/courses/find-a-course/engineering/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Swinburne University of Technology"
    uidPrefix = "AU-SWI-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "victorian certificate": "4",
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

    campuses = {
        "Hobart": "710",
        "Croydon": "708",
        "Off-Campus": "709",
        "Wantirna": "707",
        "Richmond Football Club": "706",
        "Melbourne": "704",
        "Hawthorn": "703"
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

    lua_script = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(2.0))
          local element = splash:select('button.view-more.btn.btn-secondary-outline')
          assert(element:mouse_click())
          assert(splash:wait(2.0))
          return {
            html = splash:html(),
            png = splash:png(),
            har = splash:har(),
          }
        end
    """

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//a[@title='Learn more']/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//ul[@class='list']//a[@class='card  ']/@href").getall()

        for item in sub:
            yield SplashRequest(response.urljoin(item), callback=self.link_parse, args={"wait": 20},
                                meta={'url': response.urljoin(item)})

    def link_parse(self, response):
        view_more = response.css('button.view-more.btn.btn-secondary-outline')

        if view_more:
            yield SplashRequest(response.meta['url'], callback=self.link_parse, endpoint='execute',
                                args={'lua_source': self.lua_script, 'url': response.meta['url']})
        else:
            courses = response.xpath("//a[@class='results-item']/@href").getall()

            for item in courses:
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//span[@class='course-code']/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        location = response.xpath("//span[@class='course-location']/text()").get()
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if re.search('online', location, re.I | re.M):
                study_holder.add('Online')
                campus_holder.add('709')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        overview = response.xpath("//div[@class='course-meta']/following-sibling::*//div[contains(@class, "
                                  "'general-content')]").get()
        if overview:
            course_item.set_summary(strip_tags(overview))
            course_item['overview'] = strip_tags(overview, False)

        credit = response.xpath("//h4[contains(text(), 'Credit')]/following-sibling::*").get()
        if credit:
            course_item['creditTransfer'] = strip_tags(credit, False)

        course_structure = response.xpath("//div[@id='cs-field-course-structure']/*").getall()
        if course_structure:
            course_item['courseStructure'] = strip_tags(''.join(course_structure), False)

        pathway = response.xpath("//h3[contains(text(), 'Graduate skills')]/following-sibling::*").get()
        if pathway:
            course_item["careerPathways"] = strip_tags(pathway, False)

        start_date = response.xpath("//h3[contains(text(), '2020 Start Dates')]/following-sibling::*").getall()
        if start_date:
            start_date = "".join(start_date)
        else:
            start_date = response.xpath("//h3[contains(text(), 'Start Dates')]/following-sibling::*").getall()
            if start_date:
                start_date = "".join(start_date)
        start_holder = []
        if start_date:
            for month in self.months:
                if re.search(month, start_date, re.M):
                    start_holder.append(self.months[month])
        if start_holder:
            course_item['startMonths'] = '|'.join(start_holder)

        duration = response.xpath("//h3[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration = "".join(duration)
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
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        learn = response.xpath("//h3[contains(text(), 'Course learning outcomes')]/following-sibling::*").getall()
        if len(learn) > 0:
            course_item["whatLearn"] = strip_tags("".join(learn), False)

        for header, content in zip(response.xpath("//div[@id='fees']//th/text()").getall(),
                                   response.xpath("//div[@id='fees']//td/text()").getall()):
            if re.search(r"total cost", header, re.I | re.M):
                dom_total = re.findall("(\d+?),?(\d{3})", content)
                if len(dom_total) > 0:
                    course_item["domesticFeeTotal"] = float("".join(dom_total[0]))
            if re.search(r"course per year", header, re.I | re.M):
                dom_annual = re.findall("(\d+?),?(\d{3})", content)
                if len(dom_annual) > 0:
                    course_item["domesticFeeAnnual"] = float("".join(dom_annual[0]))

        if "domesticFeeAnnual" in course_item and "domesticFeeTotal" not in course_item:
            if "durationMinFull" in course_item:
                if course_item["durationMinFull"] < 1:
                    course_item["domesticFeeTotal"] = course_item["domesticFeeAnnual"]
                else:
                    course_item["domesticFeeTotal"] = course_item["domesticFeeAnnual"] * course_item["durationMinFull"]

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        international = response.xpath("//a[@id='tab-international']/@href").get()

        if international:
            yield response.follow(international, callback=self.international_parse, meta={'item': course_item})
        else:
            yield course_item

    def international_parse(self, response):
        course_item = response.meta['item']
        course_item['internationalApps'] = 1

        cricos = response.xpath("//h3[contains(text(), 'CRICOS')]/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = cricos[0]

        fee = response.xpath("//h3[contains(text(), 'Fees')]/following-sibling::*").get()
        int_fee = []
        if fee:
            int_fee = re.findall("(\d+?),?(\d{3})(?=\s\([at])", fee, re.I | re.M)
        else:
            fee = response.xpath("//h3[contains(text(), 'Course fees')]/following-sibling::*").get()
            if fee:
                int_fee = re.findall("(\d+?),?(\d{3})(?=\s\([at])", fee, re.I | re.M)
        if len(int_fee) > 0:
            course_item["internationalFeeAnnual"] = float("".join(int_fee[0]))
        if "durationMinFull" in course_item and "internationalFeeAnnual" in course_item:
            if course_item["durationMinFull"] < 1:
                course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"]
            else:
                course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"] \
                                                       * course_item["durationMinFull"]

        yield course_item
