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

    def parse(self, response):
        pass