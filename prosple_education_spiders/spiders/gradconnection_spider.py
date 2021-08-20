# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


class GradconnectionSpiderSpider(scrapy.Spider):
    name = 'gradconnection_spider'
    start_urls = ["https://au.gradconnection.com/graduate-jobs"]

    page_num = 1

    def parse(self, response):
        employers = response.xpath("//div[@class='view-employer-jobs-count']/a/@href").getall()

        for item in employers:
            yield response.follow(item, callback=self.sub_parse, meta={'url': response.urljoin(item)})

        next_page = response.xpath("//li[contains(@class, 'rc-pagination-next')][@aria-disabled='false']").getall()
        if next_page:
            self.page_num += 1
            link = "https://au.gradconnection.com/graduate-jobs/?page=" + str(self.page_num)
            yield response.follow(link, callback=self.parse)

    def sub_parse(self, response):
        jobs = response.xpath("//div[@class='profileborder']//div[@class='employercampaignbox']//a["
                              "@class='box-header-title']/@href").getall()

        for item in jobs:
            url = response.meta['url']
            yield response.follow(item, callback=self.job_parse, meta={'url': url})

    def job_parse(self, response):
        job_item = Opportunity()

        job_item["last_update"] = date.today().strftime("%m/%d/%y")
        job_item['source_url'] = response.request.url
        job_item['application_link'] = response.request.url
        job_item['employer_url'] = response.meta['url']

        name = response.xpath("//*[@class='employers-panel-title']/text()").get()
        if name:
            job_item['employer_name'] = name.strip()

        job_name = response.xpath("//*[@class='employers-profile-h1']/text()").get()
        if job_name:
            job_item['opportunity_name'] = job_name.strip()

        overview = response.xpath(
            "//*[@class='employercampaignlanding']//*[@class='campaign-content-container']/*").getall()
        if overview:
            overview = ''.join(overview[1:])
            job_item.set_summary(strip_tags(overview))
            job_item["overview"] = strip_tags(overview, remove_all_tags=False, remove_hyperlinks=True)

        job_type = response.xpath("//*[@class='box-content-catagories-bold'][text()='Job "
                                  "type:']/following-sibling::text()").get()
        if job_type:
            job_item['opportunity_type'] = job_type.strip()

        location = response.xpath(
            "//*[@class='box-content-catagories-bold'][text()='Locations:']/following-sibling::*").get()
        if location:
            job_item['location'] = location.strip()

        close = response.xpath("//*[@class='box-content-catagories-bold'][text()='Closing "
                               "Date:']/following-sibling::text()").get()
        if close:
            job_item['application_close'] = close



        yield job_item
