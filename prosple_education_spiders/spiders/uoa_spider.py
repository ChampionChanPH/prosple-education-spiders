# -*- coding: utf-8 -*-

from ..standard_libs import *


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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


class UoaSpiderSpider(scrapy.Spider):
    name = 'uoa_spider'
    allowed_domains = ['www.adelaide.edu.au', 'adelaide.edu.au']
    start_urls = ['https://www.adelaide.edu.au/degree-finder/?v__s=&m=view&dsn=program.source_program&adv_avail_comm'
                  '=1&adv_acad_career=0&adv_degree_type=0&adv_atar=0&year=2020&adv_subject=0&adv_career=0&adv_campus'
                  '=0&adv_mid_year_entry=0']

    degrees = {
        "graduate certificate": "7",
        "adelaide graduate certificate": "7",
        "graduate diploma": "8",
        "adelaide graduate diploma": "8",
        "master": research_coursework,
        "adelaide master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "honours degree of bachelor": "3",
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
        "Waite Campus": "731",
        "Roseworthy Campus": "733",
        "Ngee Ann-Adelaide Education Centre": "732",
        "North Terrace Campus": "730",
        "Ngee Ann Academy": "728",
        "Roseworthy": "727",
        "Adelaide": "726",
        "Teaching Hospitals": "725",
        "North Terrace": "724"
    }

    def parse(self, response):
        courses = response.xpath("//div[@class='c-table']//a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of Adelaide"
        uidPrefix = "AU-UOA-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution
        # course_item["internationalApplyURL"] = response.request.url
        # course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h2/text()").get()
        course_item["courseName"] = course_name.strip()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        overview = response.xpath("//div[@class='intro-df']/div/*[following-sibling::p/strong[contains(text(), "
                                  "'What will you do?')]]").getall()
        if len(overview) > 0:
            course_item["overview"] = "".join(overview)
        else:
            overview = response.xpath("//div[@class='intro-df']/div/p").getall()
            course_item["overview"] = "".join(overview)

        summary = course_item["overview"]
        summary = re.sub("<strong.*?/strong>", "", summary)
        summary = re.sub("<.*?>", "", summary)
        course_item.set_summary(cleanspace(summary))

        learn = response.xpath("//div[@class='intro-df']/div/*[preceding-sibling::p/strong[contains(text(), "
                               "'What will you do')] and following-sibling::p/strong[contains(text(), 'Where could it"
                               " take you')]]").getall()
        if len(learn) > 0:
            course_item["whatLearn"] = "".join(learn)

        career = response.xpath("//div[@class='intro-df']/div/*[preceding-sibling::p/strong[contains(text(), "
                                "'Where could it take you')]]").getall()
        if len(career) > 0:
            course_item["careerPathways"] = "".join(career)

        duration = response.xpath("//span[preceding-sibling::span/text()='Duration']").get()
        if duration is not None:
            if re.search("year", duration, re.I | re.M):
                course_item["teachingPeriod"] = 1
            elif re.search("month", duration, re.I | re.M):
                course_item["teachingPeriod"] = 12
            duration = re.findall("(\d*?\.?\d+)(?=\s+?year|month)", duration, re.I | re.M)
            if len(duration) > 0:
                course_item["durationMinFull"] = duration[0]

        location = response.xpath("//span[preceding-sibling::span/text()='Campus']").get()
        campus_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(set(campus_holder))

        cricos = response.xpath("//span[preceding-sibling::span/text()='CRICOS']").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if len(cricos) > 0:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1

        dom_fee = response.xpath("//*[contains(text(), 'Australian Full-fee place')]/text()").get()
        csp_fee = response.xpath("//*[contains(text(), 'Commonwealth-supported place')]/text()").get()
        int_fee = response.xpath("//*[contains(text(), 'International student place')]/text()").get()
        if dom_fee is not None:
            dom_fee = re.findall("\$(\d+),?(\d{3})", dom_fee, re.M)
            if len(dom_fee) > 0:
                course_item["domesticFeeAnnual"] = "".join(dom_fee[0])
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
        if csp_fee is not None:
            csp_fee = re.findall("\$(\d+),?(\d{3})", csp_fee, re.M)
            if len(csp_fee) > 0:
                course_item["domesticSubFeeAnnual"] = "".join(csp_fee[0])
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)
        if int_fee is not None:
            int_fee = re.findall("\$(\d+),?(\d{3})", int_fee, re.M)
            if len(int_fee) > 0:
                course_item["internationalFeeAnnual"] = "".join(int_fee[0])
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        intake = response.xpath("//th[contains(text(), 'Intake')]/following-sibling::td").getall()
        start_months = []
        if len(intake) > 0:
            for item in intake:
                for month in self.months:
                    if re.search(month, item, re.M):
                        start_months.append(self.months[month])
        start_months = set(start_months)
        if len(start_months) > 0:
            course_item["startMonths"] = "|".join(start_months)

        atar = response.xpath("//th[contains(a/text(), 'Guaranteed Entry Score - ATAR')]/following-sibling::td/text()").get()
        if atar is not None:
            try:
                atar = float(atar.strip())
                course_item["guaranteedEntryScore"] = atar
            except ValueError:
                pass

        course_item.set_sf_dt(self.degrees, ["and", "with", "/"])

        if "doubleDegree" in course_item:
            yield course_item
