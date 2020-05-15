# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *


class UndSpiderSpider(scrapy.Spider):
    name = 'und_spider'
    allowed_domains = ['www.notredame.edu.au', 'notredame.edu.au']
    start_urls = ['https://www.notredame.edu.au/study/programs']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    lua = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(2.0))
          local category = splash:select(args.selector_category)
          assert(category:mouse_click())
          assert(splash:wait(2.0))
          return {
            html = splash:html(),
            }
        end
    """

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.splash_index, args={'wait': 5},
                            meta={'url': response.request.url})

    def splash_index(self, response):
        categories = response.css(".course-tiles__item::attr(id)").getall()

        for item in categories:
            selector = "#" + item + " a"
            yield SplashRequest(response.meta["url"], callback=self.program_parse, endpoint='execute',
                                args={'lua_source': self.lua, 'url': response.meta["url"],
                                      'selector_category': selector})

    def program_parse(self, response):
        courses = response.xpath("//span[@class='program-list__degree']/text()").getall()
        print(courses)