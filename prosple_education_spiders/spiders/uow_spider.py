# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *
import ast


class UowSpiderSpider(scrapy.Spider):
    name = 'uow_spider'
    # allowed_domains = ['https://coursefinder.uow.edu.au/search-results/index.html']
    start_urls = ['https://coursefinder.uow.edu.au/search-results/index.html']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Wollongong (UOW)"
    uidPrefix = "AU-UOW-"

    init_lua = """
    function main(splash, args)
      local get_div_count = splash:jsfunc([[
      function () {
        var courses = [];
        var body = document.body;
        courses.concat(body.getElementsByTagName('li.next'));
      }
      ]])
      splash:go(args.url)
    
      return ("There are %s DIVs in %s"):format(
        get_div_count(), args.url)
    end
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(10))
      local test_list = 0
      return {
        html = splash:html(),
        test = test_list
      }
    end
    """

    def start_requests(self):
        for url in self.start_urls:
            return [scrapy.FormRequest(url, callback=self.parse, errback=self.err_parse)]

    def parse(self, response):
        # yield SplashRequest(self.start_urls[0], callback=self.splash_index, args={'wait': 10})
        yield SplashRequest(self.start_urls[0], self.splash_index, endpoint='execute', args={'lua_source': self.init_lua, 'url': self.start_urls[0]})

    def err_parse(self, response):
        # yield SplashRequest(self.start_urls[0], callback=self.splash_index, args={'wait': 10})
        yield SplashRequest(self.start_urls[0], self.splash_index, endpoint='execute', args={'lua_source': self.init_lua, 'url': self.start_urls[0]})

    def splash_index(self, response):
        print(response.test)
        # courses =
        # next = response.css("li.next")
        # if next:
