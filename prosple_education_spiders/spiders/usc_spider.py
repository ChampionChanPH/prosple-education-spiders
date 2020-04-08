# -*- coding: utf-8 -*-
import scrapy


class UscSpiderSpider(scrapy.Spider):
    name = 'usc_spider'
    # allowed_domains = ['https://www.usc.edu.au/learn/courses-and-programs']
    start_urls = ['https://www.usc.edu.au/learn/courses-and-programs/', 'https://www.usc.edu.au/learn/courses-and-programs/postgraduate-degrees']

    def parse(self, response):
        pass
