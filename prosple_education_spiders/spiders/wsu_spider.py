# -*- coding: utf-8 -*-
import scrapy


class WsuSpiderSpider(scrapy.Spider):
    name = 'wsu_spider'
    allowed_domains = ['https://www.westernsydney.edu.au/future/study/courses.html']
    start_urls = ['http://https://www.westernsydney.edu.au/future/study/courses.html/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    def parse(self, response):
        pass
