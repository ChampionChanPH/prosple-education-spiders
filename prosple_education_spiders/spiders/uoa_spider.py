# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


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


class UoaSpiderSpider(scrapy.Spider):
    name = 'uoa_spider'
    allowed_domains = ['www.adelaide.edu.au', 'adelaide.edu.au']
    start_urls = ['https://www.adelaide.edu.au/degree-finder/?v__s=&m=view&dsn=program.source_program&adv_avail_comm'
                  '=1&adv_acad_career=0&adv_degree_type=0&adv_atar=0&year=2020&adv_subject=0&adv_career=0&adv_campus'
                  '=0&adv_mid_year_entry=0']

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "university foundation studies": "13",
        "non-award": "13",
        "no match": "15"
    }

    def parse(self, response):
        courses = response.xpath("//div[@class='c-table']//a/@href").getall()

        courses = [
            "https://www.adelaide.edu.au/degree-finder/2020/mml_mmaclearn.html",
            "https://www.adelaide.edu.au/degree-finder/2020/drcd_drclinden.html",
            "https://www.adelaide.edu.au/degree-finder/2020/mmesc_mmesc.html"
        ]

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
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h2/text()").get()
        course_item["courseName"] = course_name.strip()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        overview = response.xpath("//div[@class='intro-df']/div/*[following-sibling::p/strong[contains(text(), "
                                  "'What will you do?')]]").getall()
        if len(overview) > 0:
            course_item["overview"] = "".join(overview)

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
            duration = re.findall("\d*?\.?\d+(?=\s+?(year|month))", duration, re.I | re.M)
            if len(duration) > 0:
                course_item["durationMinFull"] = duration[0]
        if "durationMinFull" in course_item:
            if re.search("year", duration, re.I | re.M):
                course_item["teachingPeriod"] = 1
            elif re.search("month", duration, re.I | re.M):
                course_item["teachingPeriod"] = 12
        cricos = response.xpath("//span[preceding-sibling::span/text()='CRICOS']").get()

        dom_fee = response.xpath("//*[contains(text(), 'Australian Full-fee place')]/text()").get()
        csp_fee = response.xpath("//*[contains(text(), 'Commonwealth-supported place')]/text()").get()
        int_fee = response.xpath("//*[contains(text(), 'International student place')]/text()").get()
        if dom_fee is not None:
            dom_fee = re.findall("\$(\d+),?(\d{3})", dom_fee, re.M)
            if len(dom_fee) > 0:
                course_item["domesticFeeAnnual"] = "".join(dom_fee[0])
        if csp_fee is not None:
            csp_fee = re.findall("\$(\d+),?(\d{3})", csp_fee, re.M)
            if len(csp_fee) > 0:
                course_item["domesticSubFeeAnnual"] = "".join(csp_fee[0])
        if int_fee is not None:
            int_fee = re.findall("\$(\d+),?(\d{3})", int_fee, re.M)
            if len(int_fee) > 0:
                course_item["internationalFeeAnnual"] = "".join(int_fee[0])
                if "durationMinFull" in course_item:
                    if course_item["teachingPeriod"] == 1:
                        if course_item["durationMinFull"] < 1:
                            course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"]
                        else:
                            course_item["internationalFeeTotal"] = float(course_item["internationalFeeAnnual"]) \
                                                                   * float(course_item["durationMinFull"])

        course_item.set_sf_dt(self.degrees, ["of", "in"], ["and", "with"])

        yield course_item
