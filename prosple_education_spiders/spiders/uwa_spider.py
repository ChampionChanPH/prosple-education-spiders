# by: Johnel Bacani

from ..standard_libs import *


class UwaSpiderSpider(scrapy.Spider):
    name = 'uwa_spider'
    # allowed_domains = ['https://www.uwa.edu.au/study/courses-and-careers/find-a-course']
    start_urls = ['https://www.uwa.edu.au/study/courses-and-careers/find-a-course']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "James Cook University (JCU)"
    uidPrefix = "AU-JCU-"
    lua_loadmore = """
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(2))
      local element = splash:select('.results-action-load-more')
      while element do
        assert(element:mouse_click())
        assert(splash:wait(.2))
        element = splash:select('.results-action-load-more')
      end
      return {
        html = splash:html(),
        png = splash:png(),
        har = splash:har(),
      }
    end
    """

    degree_delims = ["and"]

    def parse(self, response):
        yield SplashRequest(self.start_urls[0], callback=self.load_more, endpoint='execute',
                            args={'lua_source': self.lua_loadmore, 'url': self.start_urls[0]},
                            meta={'url': self.start_urls[0]})

    def load_more(self, response):
        courses = response.css(".result-item")
        for item in courses:
            course = item.css("a.result-item::attr(href)").get()
            yield response.follow("https://www.uwa.edu.au"+course, callback=self.course_parse)

    def course_parse(self, response):
        print(response.css("h1::text").get())
