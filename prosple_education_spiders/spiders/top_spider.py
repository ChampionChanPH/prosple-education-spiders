# -*- coding: utf-8 -*-
import scrapy


class TopSpiderSpider(scrapy.Spider):
    name = 'top_spider'
    allowed_domains = ['']
    start_urls = ['https://www.top.edu.au/school-of-business/undergraduate-programs',
                  'https://www.top.edu.au/school-of-business/postgraduate-programs']
    banned_urls = ['https://www.top.edu.au/school-of-business/postgraduate-programs/graduate-diploma-of-public'
                   '-relations-and-marketing/graduate-diploma-of-public-relations-and-marketing',
                   'https://www.top.edu.au/school-of-business/postgraduate-programs/master-of-professional-accounting'
                   '-and-business/master-of-professional-accounting-and-business',
                   'https://www.top.edu.au/school-of-business/postgraduate-programs/master-of-marketing-and-public'
                   '-relations--/master-of-marketing-and-public-relations']

    def parse(self, response):
        courses = response.xpath("//div[@id='main-content']/ul/li/a/@href").getall()

        for item in courses:
            if item not in self.banned_urls:
                yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        yield item
