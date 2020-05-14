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


class AnuCsppSpiderSpider(scrapy.Spider):
    name = 'anu_cspp_spider'
    allowed_domains = ['crawford.anu.edu.au', 'programsandcourses.anu.edu.au']
    start_urls = ['https://crawford.anu.edu.au/study/graduate-degrees']
    banned_urls = ['/study/graduate-degrees/phd-programs']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Crawford School of Public Policy"
    uidPrefix = "AU-ANU-CSPP-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Hobart": "43956",
        "Eveleigh": "43955"
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
        courses = response.xpath("//div[contains(@class, 'panel-display')]//a/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        next_page = response.xpath("//a[contains(text(), 'degree program structure, admission requirements and "
                                   "academic information')]/@href").get()

        if next_page is not None:
            yield SplashRequest(next_page, callback=self.course_parse, args={'wait': 10.0},
                                meta={'url': next_page})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta['url']

        course_name = response.xpath("//span[@class='intro__degree-title__component']/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@class='introduction']/*").getall()
        if len(overview) > 0:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, False)

        career = response.xpath("//*[preceding-sibling::*[contains(text(), 'Career Options')]]").getall()
        if len(career) > 0:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(career, False)

        learn = response.xpath("//*[preceding-sibling::*[contains(text(), 'Learning Outcomes')]]").get()
        if learn is not None:
            course_item["whatLearn"] = strip_tags(learn, False)

        structure = response.xpath("//*[preceding-sibling::*[contains(text(), 'Program Requirements')]]").getall()
        if len(structure) > 0:
            structure = "".join(structure)
            course_item["courseStructure"] = strip_tags(structure, False)

        duration = response.xpath("//span[contains(text(), 'Length')]/following-sibling::*/text()").get()
        if duration is not None:
            duration = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration, re.M)
            if duration is not None:
                if len(duration) > 0:
                    course_item["durationMinFull"] = float(duration[0][0])
                    self.get_period(duration[0][1], course_item)

        dom_fee = response.xpath("//dt[contains(text(), 'Annual indicative fee for domestic "
                                 "students')]/following-sibling::*").get()
        if dom_fee is not None:
            dom_fee = re.findall("\$\d*,?\d+", dom_fee, re.M)
            if len(dom_fee) > 0:
                dom_fee = float(re.sub("[$,]", "", dom_fee[0]))
                course_item["domesticFeeAnnual"] = dom_fee
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//dt[contains(text(), 'Annual indicative fee for international "
                                 "students')]/following-sibling::*").get()
        if int_fee is not None:
            int_fee = re.findall("\$\d*,?\d+", int_fee, re.M)
            if len(int_fee) > 0:
                int_fee = float(re.sub("[$,]", "", int_fee[0]))
                course_item["internationalFeeAnnual"] = int_fee
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        course_code = response.xpath("//*[preceding-sibling::*[contains(text(), 'Academic plan')]]/text()").get()
        if course_code is not None:
            course_item["courseCode"] = course_code.strip()

        nominal = response.xpath("//*[preceding-sibling::*[contains(text(), 'Post Nominal')]]/text()").get()
        if nominal is not None:
            if nominal.strip() != "":
                course_item["postNumerals"] = nominal.strip()

        cricos = response.xpath("//*[preceding-sibling::*[contains(text(), 'CRICOS')]]/text()").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M | re.I)
            if len(cricos) > 0:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.meta['url']

        study_holder = []
        study = response.xpath("//*[preceding-sibling::*[contains(text(), 'Mode of delivery')]]/text()").getall()
        if len(study) > 0:
            study = "".join(study)
            if re.search("In Person", study, re.I | re.M):
                study_holder.append("In Person")
            if re.search("Online", study, re.I | re.M):
                study_holder.append("Online")
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)

        entry = response.xpath("//*[not(self::div)][preceding-sibling::*[contains(text(), 'Admission Requirements')]]").getall()
        if len(entry) > 0:
            entry = "".join(entry)
            course_item["entryRequirements"] = strip_tags(entry, False)

        course_item["campusNID"] = "569"

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item
