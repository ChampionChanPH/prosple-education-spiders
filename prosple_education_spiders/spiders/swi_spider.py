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


class SwiSpiderSpider(scrapy.Spider):
    name = 'swi_spider'
    allowed_domains = ['www.swinburne.edu.au', 'swinburne.edu.au']
    start_urls = ['https://www.swinburne.edu.au/study/find-a-course']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    courses = []

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

    institution = "Swinburne University of Technology"
    uidPrefix = "AU-SWI-"

    def parse(self, response):
        categories = response.xpath("//div[contains(@class, 'teaser-wrap')]//a/@href").getall()

        for item in categories:
            yield SplashRequest(response.urljoin(item).strip("/"), callback=self.sub_parse, args={"wait": 5})

    def sub_parse(self, response):
        sub = response.xpath("//div[@class='discipline-link-list']//a/@href").getall()

        if len(sub) > 0:
            for item in sub:
                yield SplashRequest(response.urljoin(item), callback=self.sub_parse, args={"wait": 5})
        else:
            self.courses.extend(response.xpath("//div[contains(@class, 'course-list')]//a/@href").getall())

        courses = set(self.courses)

        courses = ["https://www.swinburne.edu.au/study/course/time-and-priority-management/",
                   "https://www.swinburne.edu.au/study/course/bachelor-of-engineering-honours-bachelor-of-innovation-and-design/telecommunications/"]
        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        course = response.xpath("//h1/text()").get()
        course_sub = response.xpath("//h1/following-sibling::h2/text()").get()
        if course_sub is not None:
            course_item.set_course_name(course.strip() + " " + course_sub.strip(), self.uidPrefix)
        else:
            course_item.set_course_name(course.strip(), self.uidPrefix)

        course_code = response.xpath("//span[@class='course-code']/text()").get()
        if course_code is not None:
            course_item["courseCode"] = course_code.strip()

        location = response.xpath("//span[@class='course-location']/text()").get()
        campus_holder = []
        study_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
            if re.search("online", location, re.I | re.M):
                study_holder.append("Online")
                campus_holder.append("709")
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(set(campus_holder))
            study_holder.append("In Person")
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)

        overview = response.xpath("//h3[contains(text(), 'Course description')]/following-sibling::*").get()
        if overview is not None:
            course_item["overview"] = strip_tags(overview, False)

        credit = response.xpath("//h4[contains(text(), 'Credit')]/following-sibling::*").get()
        if credit is not None:
            course_item["creditTransfer"] = strip_tags(credit, False)

        course_structure = response.xpath("//h3[contains(text(), 'Course structure')]/following-sibling::*").get()
        if course_structure is not None:
            course_item["courseStructure"] = strip_tags(course_structure, False)

        pathway = response.xpath("//h3[contains(text(), 'Graduate skills')]/following-sibling::*").get()
        if pathway is not None:
            course_item["careerPathways"] = strip_tags(pathway, False)

        start_date = response.xpath("//h3[contains(text(), '2020 Start Dates')]/following-sibling::*").getall()
        if len(start_date) > 0:
            start_date = "".join(start_date)
        else:
            start_date = response.xpath("//h3[contains(text(), 'Start Dates')]/following-sibling::*").getall()
            if len(start_date) > 0:
                start_date = "".join(start_date)
        start_holder = []
        if len(start_date) > 0:
            for month in self.months:
                if re.search(month, start_date, re.M):
                    start_holder.append(self.months[month])
        if len(start_holder) > 0:
            course_item["startMonths"] = "|".join(start_holder)

        duration = response.xpath("//h3[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration is not None:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration)
            if len(duration_full) == 1:
                for period in self.teaching_periods:
                    if re.search(period, duration_full[0][1], re.I):
                        course_item["teachingPeriod"] = self.teaching_periods[period]
                        course_item["durationMinFull"] = float(duration_full[0][0])
            if len(duration_full) > 1:
                course_item["teachingPeriod"] = 1
                for period in self.teaching_periods:
                    if re.search(period, duration_full[0][1], re.I):
                        course_item["durationMinFull"] = float(duration_full[0][0]) / self.teaching_periods[period]
                    if re.search(period, duration_full[1][1], re.I):
                        course_item["durationMinPart"] = float(duration_full[1][0]) / self.teaching_periods[period]

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

        course_item.set_sf_dt(self.degrees, ["and", "/"])

        international = response.xpath("//a[@id='tab-international']/@href").get()

        if international is not None:
            yield response.follow(international, callback=self.international_parse, meta={'item': course_item})
            return

        yield course_item

    def international_parse(self, response):
        course_item = response.meta['item']
        course_item["internationalApps"] = 1

        cricos = response.xpath("//h3[contains(text(), 'CRICOS')]/following-sibling::*").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if len(cricos) > 0:
                course_item["cricosCode"] = cricos[0]

        fee = response.xpath("//h3[contains(text(), 'Fees')]/following-sibling::*").get()
        int_fee = []
        if fee is not None:
            int_fee = re.findall("(\d+?),?(\d{3})(?=\s\([at])", fee, re.I | re.M)
        else:
            fee = response.xpath("//h3[contains(text(), 'Course fees')]/following-sibling::*").get()
            if fee is not None:
                int_fee = re.findall("(\d+?),?(\d{3})(?=\s\([at])", fee, re.I | re.M)
        if len(int_fee) > 0:
            course_item["internationalFeeAnnual"] = float("".join(int_fee[0]))
        if "durationMinFull" in course_item and "internationalFeeAnnual" in course_item:
            if course_item["durationMinFull"] < 1:
                course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"]
            else:
                course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"]\
                                                       * course_item["durationMinFull"]

        yield course_item



