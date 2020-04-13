# -*- coding: utf-8 -*-
import scrapy


class UodSpiderSpider(scrapy.Spider):
    name = 'uod_spider'
    allowed_domains = ['divinity.edu.au']
    start_urls = ['https://divinity.edu.au/study/courses/']

    def parse(self, response):
        courses = response.xpath("//div[@class='entry-content']//li/a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        pass