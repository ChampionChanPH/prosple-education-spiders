# -*- coding: utf-8 -*-
# by Christian Anasco
from ..standard_libs import *


class SwiSpiderSpider(scrapy.Spider):
    name = 'swi_spider'
    allowed_domains = ['www.swinburne.edu.au', 'swinburne.edu.au']
    start_urls = ['https://www.swinburne.edu.au/study/find-a-course']

    sub_category = []
    courses = []

    init_lua = """
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(5))
      return {
        html = splash:html()
      }
    end
    """

    def parse(self, response):
        categories = response.xpath("//div[contains(@class, 'teaser-wrap')]//a/@href").getall()

        for item in categories:
            # yield SplashRequest(response.urljoin(item).strip("/"), callback=self.sub_parse, args={"wait": 5})
            yield SplashRequest(response.urljoin(item), callback=self.sub_parse, endpoint='execute',
                                args={'lua_source': self.init_lua, 'url': response.urljoin(item)})

    def sub_parse(self, response):
        sub = response.xpath("//div[@class='discipline-link-list']//a/@href").getall()

        if len(sub) > 0:
            for item in sub:
                yield SplashRequest(response.urljoin(item), callback=self.sub_parse, args={"wait": 5})
        else:
            courses = response.xpath("//div[contains(@class, 'course-list')]//a/@href").getall()
            for course in courses:
                yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        print(response.xpath("//h1[@id='course-title']/text()").get())



