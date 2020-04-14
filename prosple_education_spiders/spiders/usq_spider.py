# -*- coding: utf-8 -*-
import scrapy


class UsqSpiderSpider(scrapy.Spider):
    name = 'usq_spider'
    allowed_domains = ['https://www.usq.edu.au/study']
    start_urls = ['https://www.usq.edu.au/study/']

    def parse(self, response):
        pass
