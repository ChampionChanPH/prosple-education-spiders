# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest

class TestSpider(scrapy.Spider):
    name = 'test'
    # allowed_domains = ['https://study.curtin.edu.au/offering/course-ug-bachelor-of-science-biomedical-science-honours--bh-biomedv1/']
    start_urls = ['https://study.curtin.edu.au/offering/course-ug-bachelor-of-science-biomedical-science-honours--bh-biomedv1/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'


    def parse(self, response):
        script = """
            function main(splash)
                local button = splash:select(".personalisation-toggle span.ico-au")
                button:mouse_click()
                splash:wait(2.0)
                local button = splash:select("div.radio-group--full-width button:not(active)")
                button:mouse_click()
                splash:wait(4.0)
                return {html = splash:html()}
            end
        """
        script2 = """
            function main(splash)
                splash:go("https://study.curtin.edu.au/offering/course-ug-bachelor-of-science-health-sciences-honours--bh-hlthscv1/")
                splash:wait(0.5)
                local title = splash:evaljs("document.title")
                return {title=title}
            end
        """
        script3 = """
                    
            function main(splash)
                return {hello="world!"}
            end
        """

        print("URL: ",response.request.url)
        yield SplashRequest(response.request.url, callback=self.testparse, endpoint="execute", args={'lua_source': script3})
        # print(response)

    def testparse(self, response):
        print("hello")
        print(response.keys())