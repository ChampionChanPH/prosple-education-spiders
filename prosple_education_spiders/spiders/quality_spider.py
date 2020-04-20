# -*- coding: utf-8 -*-
import scrapy


class QualitySpiderSpider(scrapy.Spider):
    name = 'quality_spider'
    # allowed_domains = ['https://www.compared.edu.au/browse-institutions']
    start_urls = ['https://www.compared.edu.au/browse-institutions/']

    def parse(self, response):
        pass
