# -*- coding: utf-8 -*-
import scrapy
from ..items import Scholarship
from ..misc_functions import *

class ScunsSpiderSpider(scrapy.Spider):
    name = 'sc_uns_spider'
    # allowed_domains = ['https://www.scholarships.unsw.edu.au/scholarships/search?show=open']
    start_urls = ['https://www.scholarships.unsw.edu.au/scholarships/search?show=all']
    code = "AU-SCUNS-"
    institution = "University of New South Wales (UNSW)"
    def parse(self, response):
        rows = response.css(".rows-content")
        for row in rows:
            closed = row.css(".col-7 .row-content-inner-span").get()
            # print([closed])
            if "Closed" not in closed:
                item = Scholarship()

                opens = row.css(".col-5 div.row-content-inner-span::text").get()
                if opens:
                    item["opens"] = cleanspace(opens)

                closes = row.css(".col-6 div.row-content-inner-span::text").get()
                if closes:
                    item["closes"] = cleanspace(closes)

                details_page = row.css(".col-1 a::attr(href)").get()
                # print(details_page)
                yield response.follow(details_page, callback=self.details_parse, meta={"item": item})

    def details_parse(self, response):
        item = response.meta["item"]
        item["source_url"] = response.request.url
        item["provider_name"] = self.institution

        name = response.css("h1.scholarships-title::text").get()
        if name:
            item["name"] = cleanspace(name)

        code = response.css("h2::text").get()
        if code:
            item["code"] = cleanspace(code)
            item["identifier"] = self.code+code

        else:
            item["identifier"] = self.code + name

        value = response.css(".scholarships-table-value .content::text").get()
        if value:
            item["total_value"] = value

        overview = response.css(".scholarships-outline").get()
        if overview:
            item["overview"] = overview

        eligibility = response.css(".scholarships-eligibility").get()
        if eligibility:
            item["eligibility"] = eligibility

        criteria = response.css(".scholarships-selection").get()
        if criteria:
            item["criteria"] = criteria

        app_process = response.css(".scholarships-interviews").get()
        if app_process:
            item["app_process"] = app_process


        yield item