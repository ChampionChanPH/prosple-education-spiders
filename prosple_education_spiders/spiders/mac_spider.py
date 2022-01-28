# -*- coding: utf-8 -*-
# by Christian Anasco
# having difficulties getting the courses

from ..standard_libs import *
from ..scratch_file import strip_tags


class MacSpiderSpider(scrapy.Spider):
    name = 'mac_spider'
    allowed_domains = ['courses.mq.edu.au', 'mq.edu.au']
    start_urls = ['https://courses.mq.edu.au/search?query=&refinementList%5Byear%5D%5B0%5D=2020&refinementList'
                  '%5Bdomestic%5D%5B0%5D=true&configure%5BhitsPerPage%5D=1000&configure%5BmaxValuesPerFacet%5D=100']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.sub_parse, args={'wait': 20})

    def sub_parse(self, response):
        title = response.xpath("//title/text()").get()
        courses = response.xpath("//div[contains(@class, 'table-listing')]//a/@href").getall()
        print(title)
        print(courses)