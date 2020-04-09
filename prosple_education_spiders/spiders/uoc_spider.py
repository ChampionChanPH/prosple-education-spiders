# -*- coding: utf-8 -*-
import scrapy


class UocSpiderSpider(scrapy.Spider):
    name = 'uoc_spider'
    allowed_domains = ['search.canberra.edu.au', 'www.canberra.edu.au', 'canberra.edu.au']
    start_urls = ['http://https://search.canberra.edu.au/s/search.html?collection=courses&form=course-search&profile'
                  '=_default&query=!padre&course-search-widget__submit=&meta_C_and=COURSE&sort=metaH/']

    def parse(self, response):
        pass
