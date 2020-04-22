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
        card_selector = "div.clearFix app-study-area-card"
        for institution in [response.urljoin(x) for x in institutions]:
            yield SplashRequest(institution, self.institution_scrape, endpoint='execute', args={'lua_source': self.lua, 'url': institution}, meta={'card_selector': card_selector, 'level': level, 'url': institution, 'studyField': "Overall"})

    def institution_scrape(self, response):
        quality_item = Rating()
        institution = response.css("a.text-tertiary::text").extract_first()
        if institution:
            quality_item["institution"] = institution
        else:
            quality_item["institution"] = response.css("h1::text").extract_first()
        quality_item["url"] = response.meta["url"]
        quality_item["level"] = response.meta["level"]
        quality_item["studyField"] = response.meta["studyField"]
        study_fields = response.css(".study-area-name")
        done = []
        if study_fields:
            card_selector = "app-study-area-card.display-flex-sml"
            for field in study_fields:
                link = field.css("a::attr(href)").extract_first()
                link = response.urljoin(link)
                if link not in done:
                    done.append(link)
                    study_field_name = field.css("strong::text").extract_first()
                    yield SplashRequest(link, self.institution_scrape, args={'wait': 10}, meta={'card_selector': card_selector, 'level': response.meta["level"], 'url': link, 'studyField': study_field_name})

        cards = response.css(response.meta["card_selector"])
        # print(cards)
        for card in cards:
            current_label = card.css("b::text").extract_first()
            if current_label in list(self.labels.keys()):
                value = card.css("span.gamma span::text").extract_first()
                value = re.findall("[\d\.,]+",value)[0]
                value = value.replace(",", "")
                field = self.labels[current_label]
                quality_item[field] = value

        yield quality_item
