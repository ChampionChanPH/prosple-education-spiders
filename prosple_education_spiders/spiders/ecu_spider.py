# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import Course
from datetime import date

class EcuSpiderSpider(scrapy.Spider):
    name = 'ecu_spider'
    start_urls = ['https://www.ecu.edu.au/degrees/undergraduate'

    ]

    def parse(self, response):
        courses = response.css('ul.courseList__content').extract()

        for course in courses:
            print(course)
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["group"] = 23

        yield course_item