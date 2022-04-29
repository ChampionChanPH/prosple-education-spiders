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


class UocSpiderSpider(scrapy.Spider):
    name = 'uoc_spider'
    start_urls = ["https://www.canberra.edu.au/future-students/study-at-uc/find-a-course/view-all-courses"]
    institution = "University of Canberra"
    uidPrefix = "AU-UOC-"
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,  # One course "Honours in Information Sciences" not captured, manually
        # updated
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "university foundation studies": "13",
        "non-award": "13",  # "University of Canberra International Foundation Studies" not captured, manually
        # updated
        "no match": "15"
    }

    campuses = {
        "Singapore": "738",
        "Canberra": "735",
        "Sydney": "737"
    }

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.splash_parse, args={'wait': 20})

    def splash_parse(self, response):
        courses = response.xpath("//td/a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@id='page-title']/text()").get()
        if re.search("\(", course_name):
            course_name, course_code = re.findall("(.*) \((.*)\)$", course_name, re.I | re.M)[0]
            course_item.set_course_name(course_name.strip(), self.uidPrefix)
            course_item["courseCode"] = course_code
        else:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        cricos = response.xpath("//table[@class='course-details-table']//tr/th[contains(text(), "
                                "'CRICOS')]/following-sibling::td").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos)
            if len(cricos) > 0:
                course_item["cricosCode"] = cricos[0]
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        campus_holder = []
        location = response.xpath("//table[@class='course-details-table']//tr/th[contains(text(), "
                                  "'Location')]/following-sibling::td").get()
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(set(campus_holder))

        course_item.set_sf_dt(self.degrees)

        career = response.xpath("//div[@id='introduction']/h2[contains(text(), 'Career "
                                "opportunities')]/following-sibling::ul").get()
        if career is not None:
            course_item["careerPathways"] = career

        overview = response.xpath("//div[@id='introduction']//h2[contains(text(), 'Study a')]/preceding::p").getall()
        if len(overview) == 0:
            overview = response.xpath("//div[@id='introduction']/h2[contains(text(), "
                                      "'Introduction')]/following-sibling::p").getall()
            if len(overview) > 0:
                overview = "".join(overview)
                course_item["overview"] = strip_tags(overview, False)
        else:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, False)

        learn = response.xpath("//div[@id='introduction']//h2[contains(text(), 'Study "
                               "a')]/following-sibling::ul").get()
        if learn:
            course_item["whatLearn"] = learn

        for header, content in zip(response.xpath("//div[@id='fees']//table//tr/th/text()").getall(),
                                   response.xpath("//div[@id='fees']//table//tr/td/text()").getall()):
            if re.search("domestic", header, re.I):
                dom_fee = re.findall("\$(\d+),?(\d{3})", content)
                if len(dom_fee) > 0:
                    course_item["domesticFeeAnnual"] = "".join(dom_fee[0])
            if re.search("international", header, re.I):
                int_fee = re.findall("\$(\d+),?(\d{3})", content)
                if len(int_fee) > 0:
                    course_item["internationalFeeAnnual"] = "".join(int_fee[0])

        entry = response.xpath("//div[@id='admission']/h2[contains(text(), 'Admission')]/following-sibling::p[1]").get()
        if entry:
            course_item["entryRequirements"] = entry

        yield course_item