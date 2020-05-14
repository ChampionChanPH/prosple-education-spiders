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


class TopSpiderSpider(scrapy.Spider):
    name = 'top_spider'
    allowed_domains = ['www.top.edu.au', 'top.edu.au']
    start_urls = ['https://www.top.edu.au/school-of-business/undergraduate-programs',
                  'https://www.top.edu.au/school-of-business/postgraduate-programs']
    banned_urls = ['/school-of-business/postgraduate-programs/graduate-diploma-of-public-relations-and-marketing'
                   '/graduate-diploma-of-public-relations-and-marketing',
                   '/school-of-business/postgraduate-programs/master-of-professional-accounting-and-business/master'
                   '-of-professional-accounting-and-business',
                   '/school-of-business/postgraduate-programs/master-of-marketing-and-public-relations--/master-of'
                   '-marketing-and-public-relations',
                   '/school-of-business/postgraduate-programs/pathway-to-the-university-of-newcastle/pathway-to-the'
                   '-university-of-newcastle']
    institution = "Top Education Institute"
    uidPrefix = "AU-TOP-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
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
        courses = response.xpath("//div[@id='main-content']/ul/li//a/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
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

        cricos = response.xpath("//td[contains(strong/text(), 'CRICOS')]/following-sibling::*").get()
        if cricos is None:
            cricos = response.xpath("//strong[contains(text(), 'CRICOS')]").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M | re.I)
            if len(cricos) > 0:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        duration = response.xpath("//td[contains(strong/text(), 'Duration')]/following-sibling::*").get()
        if duration is not None:
            duration = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration, re.M)
        if duration is not None:
            if len(duration) > 0:
                course_item["durationMinFull"] = float(duration[0][0])
                self.get_period(duration[0][1], course_item)

        overview = response.xpath("//td[contains(strong/text(), 'Program Overview')]/following-sibling::*").get()
        if overview is None:
            overview = response.xpath("//td[contains(span/strong/text(), 'Program Overview')]/following-sibling::*").get()
        if overview is None:
            overview = response.xpath("//td[contains(strong/span/text(), 'Program Overview')]/following-sibling::*").get()
        if overview is None:
            overview = response.xpath("//td[contains(span/strong/em/text(), 'Program Overview')]/following-sibling::*").get()
        if overview is None:
            course_item.add_flag("overview", "no overview found: " + response.request.url)
        else:
            course_item["overview"] = strip_tags(overview, False)

        career = response.xpath("//td[contains(strong/text(), 'Career Options')]/following-sibling::*").get()
        if career is not None:
            course_item["careerPathways"] = strip_tags(career, False)

        credit = response.xpath("//td[contains(strong/text(), 'Credit arrangement')]/following-sibling::*").get()
        if credit is not None:
            course_item["creditTransfer"] = strip_tags(credit, False)

        entry = response.xpath("//td[contains(strong/text(), 'Entry Requirements')]/following-sibling::*").get()
        if entry is not None:
            course_item["entryRequirements"] = strip_tags(entry, False)

        delivery = response.xpath("//td[contains(strong/text(), 'Delivery Site')]/following-sibling::*").get()
        campus_holder = []
        study_holder = []
        if delivery is not None:
            if re.search(r"On campus", delivery, re.M | re.I):
                study_holder.append("In Person")
            if re.search(r"Online", delivery, re.M | re.I):
                study_holder.append("Online")
            for campus in self.campuses:
                if re.search(campus, delivery, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)

        learn = response.xpath("//td[contains(strong/text(), 'Learning Outcomes')]/following-sibling::*").get()
        if learn is not None:
            course_item["whatLearn"] = strip_tags(learn, False)

        structure = response.xpath("//td[contains(strong/text(), 'Course Structure')]/following-sibling::*").get()
        if structure is None:
            structure = response.xpath("//td[contains(strong/span/text(), 'Course Structure')]/following-sibling::*").get()
        if structure is not None:
            course_item["courseStructure"] = strip_tags(structure, False)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item



