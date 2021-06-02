# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import strip_tags


class Opportunity(scrapy.Item):
    opportunity_name = scrapy.Field()


class InternshalaSpiderSpider(scrapy.Spider):
    name = 'internshala_spider'
    start_urls = ['https://internshala.com/internships/page-1']

    def parse(self, response):
        total_jobs = response.xpath(
            "//div[@id='internship_seo_heading_container']/div[contains(@class, 'heading')]").get()
        if total_jobs:
            total_jobs = int(re.findall('(\d+) total internship', total_jobs)[0])
            if total_jobs:
                for num in range(1, total_jobs + 1):
                    url = f'https://internshala.com/internships/page-{num}'
                    yield response.follow(url, callback=self.sub_parse)

    def sub_parse(self, response):
        jobs = response.xpath("//a[@class='view_detail_button']/@href").getall()

        for item in jobs:
            yield response.follow(item, callback=self.job_parse)

    def job_parse(self, response):
        job_item = Opportunity()

        job_name = response.xpath("//div[contains(@class, 'heading_title')]/text()").get()
        if job_name:
            job_item['opportunity_name'] = job_name.strip()

        yield job_name
