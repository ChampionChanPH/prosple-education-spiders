import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date
from scrapy_splash import SplashRequest


class UosSpiderSpider(scrapy.Spider):
    name = 'uos_spider'
    allowed_domains = ['www.sydney.edu.au', 'sydney.edu.au']
    start_urls = ['https://www.sydney.edu.au/courses/search.html?search-type=course&page=1']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    def parse(self, response):
        return SplashRequest(response.request.url, callback=self.course_parse, args={"wait": 20, "timeout": 60})

    def course_parse(self, response):
        # courses = response.getall()
        test = response.xpath("//div[contains(@class, 'b-result-container__content')]//a/@href").getall()
        print(test)
        print(response)