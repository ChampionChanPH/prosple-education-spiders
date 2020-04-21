# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *
from ..items import Rating

class QualitySpiderSpider(scrapy.Spider):
    name = 'quality_spider'
    # allowed_domains = ['https://www.compared.edu.au/browse-institutions']
    start_urls = ['https://www.compared.edu.au/browse-institutions/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    lua = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(5))
          local element = splash:select('button.btn-comparing')
          local bounds = element:bounds()
          assert(element:mouse_click())
          assert(splash:wait(5))
          return {
            html = splash:html()
          }
        end
    """

    index_lua = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(10))
          local element = splash:select('.ng-tns-c8-4 .mat-select-arrow')
          local bounds = element:bounds()
          assert(element:mouse_click())
          assert(splash:wait(5))
          local element = splash:select('.mat-option[aria-selected=false]')
          local bounds = element:bounds()
          assert(element:mouse_click())
          assert(splash:wait(5))
          
          return {
            html = splash:html()
          }
        end
    """

    labels = {
        "experience": "overallQuality",
        "development": "skillsDevelopment",
        "teaching": "teachingQuality",
        "interactions": "learnerEngagement",
        "resources": "learningResources",
        "support": "studentSupport",
        "skills improved": "skillsScale",
        "satisfied": "overallSatisfaction",
        "teaching practices": "teachingScale",
        "full time employment": "fullTimeEmployment",
        "employment": "overallEmployment",
        "study full-time": "fullTimeStudy",
        "Median salary": "medianSalary"
    }

    download_delay = 5

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.splash_index, args={'wait': 10})
        yield SplashRequest(response.request.url, self.splash_index, endpoint='execute', args={'lua_source': self.index_lua, 'url': response.request.url})

    def splash_index(self, response):
        level = response.css(".ng-tns-c8-4::text").extract_first()
        institutions = response.css("a.text-secondary::attr(href)").extract()
        for institution in [response.urljoin(x) for x in institutions]:
            yield SplashRequest(institution, self.institution_scrape, endpoint='execute', args={'lua_source': self.lua, 'url': institution}, meta={'level': level, 'url': institution})

    def institution_scrape(self, response):
        quality_item = Rating()
        quality_item["institution"] = response.css("h1::text").extract_first()
        quality_item["url"] = response.meta["url"]
        quality_item["level"] = response.meta["level"]
        study_fields = response.css(".study-area-name strong::text").extract()
        quality_item["studyFields"] = list(set(study_fields))
        cards = response.css("div.clearFix app-study-area-card")

        for card in cards:
            current_label = card.css("b::text").extract_first()
            if current_label in list(self.labels.keys()):
                value = card.css("span.gamma span::text").extract_first()
                value = re.findall("[\d\.,]+",value)[0]
                value = value.replace(",", "")
                field = self.labels[current_label]
                quality_item[field] = value

        yield quality_item
