import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class UotSpiderSpider(scrapy.Spider):
    name = 'uot_spider'
    allowed_domains = ['www.utas.edu.au', 'utas.edu.au']
    start_urls = ['https://www.utas.edu.au/courses/undergraduate',
                  'https://www.utas.edu.au/courses/postgraduate']

    def parse(self, response):
        courses = response.xpath("//div[@id='courseList']//div[@class='content-border']//a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item