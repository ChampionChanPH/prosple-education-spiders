# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *


class ApeSpiderSpider(scrapy.Spider):
    name = 'ape_spider'
    # allowed_domains = ['https://www.apeiro.edu.au/courses']
    start_urls = ['https://www.apeiro.edu.au/courses']

    institution = "Apeiro Institute"
    uidPrefix = "AU-APE-"

    degrees = {
        "advance diploma": "5",
        "certificate iii": "4",
        "certificate iv": "4"
    }

    def parse(self, response):
        courses = response.css(".link-btn::attr(href)").getall()
        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h2::text").get()
        name = name.replace("\xa0", " ")
        if "-" in name:
            course_item["courseCode"] = name.split(" - ")[0]
            course_item.set_course_name(name.split(" - ")[1], self.uidPrefix)

        else:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees)
        #override canonical group
        course_item["canonicalGroup"] = "StudyPerth"
        course_item["group"] = 23

        overview = response.css(".course-detail-para::text").get()
        if overview:
            overview = cleanspace(overview).split(" - ")[-1]
            course_item["overview"] = overview
            course_item.set_summary(overview)

        cricos = response.css(".tba-code span::text").get()
        if cricos:
            cricos = re.findall("\d+", cricos)
            course_item["cricosCode"] = cricos[0]
            course_item["internationalApps"] = 1
            course_item["internationalApplyURL"] = response.request.url

        intakes = response.xpath("//td[preceding-sibling::td/text()=' Intakes:']/text()").getall()
        if intakes:
            intakes = " ".join(intakes).split(" ")
            intakes = [cleanspace(x).strip(",") for x in intakes if cleanspace(x) != ""]
            intakes = convert_months(intakes)
            course_item["startMonths"] = "|".join(intakes)

        course_item["modeOfStudy"] = "In person"
        course_item["campusNID"] = "37667"

        duration = response.xpath("//td[preceding-sibling::td/text()=' Duration:']/strong/text()").get()
        if duration:
            duration = re.findall("^\d+", duration)[0]
            course_item["durationMinFull"] = duration
            course_item["teachingPeriod"] = 52

        entry = response.xpath("//ul[preceding-sibling::h3/text()='Entry Requirements:']").get()
        if entry:
            course_item["entryRequirements"] = entry

        credit = response.xpath("//p[preceding-sibling::h3/text()='Recognition Of Prior Learning(RPL)']").get()
        if credit:
            course_item["creditTransfer"] = credit

        structure = response.css(".course-con").get()
        if structure:
            structure = re.findall("</h3>(.(?s)*)</div>", structure)[0]
            course_item["courseStructure"] = structure

        pathways = response.xpath("//div[child::h3/text()='Career Outcome']").get()
        if pathways:
            pathways = re.findall("</h3>(.(?s)*)</div>", pathways)[0]
            course_item["careerPathways"] = pathways




        yield course_item

