# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import strip_tags


class Opportunity(scrapy.Item):
    opportunity_name = scrapy.Field()
    employer_name = scrapy.Field()
    location = scrapy.Field()
    duration = scrapy.Field()
    stipend = scrapy.Field()
    start_date = scrapy.Field()
    apply_by = scrapy.Field()
    employer_website = scrapy.Field()
    employer_description = scrapy.Field()
    job_description = scrapy.Field()
    vacancies = scrapy.Field()


class InternshalaSpiderSpider(scrapy.Spider):
    name = 'internshala_spider'
    start_urls = ['https://internshala.com/internships/page-1']

    def parse(self, response):
        total_jobs = response.xpath(
            "//div[@id='internship_seo_heading_container']/div[contains(@class, 'heading')]").get()
        if total_jobs:
            total_jobs = int(re.findall('(\d+) total internship', total_jobs)[0])
            if total_jobs:
                total_pages = total_jobs // 40
                for num in range(1, total_pages + 2):
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

        employer_name = response.xpath("//a[@class='link_display_like_text']/text()").get()
        if employer_name:
            job_item['employer_name'] = employer_name.strip()

        location = response.xpath("//a[@class='location_link']/text()").getall()
        if location:
            job_item['location'] = '|'.join(location)

        duration = response.xpath("//div[@class='item_heading'][span/text()='Duration']/following-sibling::*["
                                  "@class='item_body']/text()").get()
        if duration:
            job_item['duration'] = duration.strip()

        stipend = response.xpath("//*[@class='stipend']/text()").get()
        if stipend:
            job_item['stipend'] = stipend.strip()

        start = response.xpath("//*[@class='start_immediately_desktop']/text()").get()
        if not start:
            start = response.xpath("//div[@class='item_heading'][contains(span/text(), 'Start "
                                   "Date')]/following-sibling::*[@class='item_body']//text()").get()
        if start:
            job_item['start_date'] = start.strip()

        apply = response.xpath("//div[@class='item_heading'][contains(span/text(), 'Apply By')]/following-sibling::*["
                               "@class='item_body']//text()").get()
        if apply:
            job_item['apply_by'] = apply.strip()

        employer_website = response.xpath("//*[@class='text-container website_link']/a/@href").get()
        if employer_website:
            job_item['employer_website'] = employer_website.strip()

        employer_description = response.xpath("//*[@class='text-container website_link']/following-sibling::*[1]").get()
        if employer_description:
            job_item['employer_description'] = strip_tags(employer_description, remove_all_tags=False,
                                                          remove_hyperlinks=True)

        job_description = response.xpath("//*[contains(@class, 'section_heading')][text()='About the internship' or "
                                         "text()='About the work from home job/internship']/following-sibling::*["
                                         "1]").get()
        if job_description:
            job_item['job_description'] = strip_tags(job_description, remove_all_tags=False,
                                                     remove_hyperlinks=True)

        vacancies = response.xpath("//*[contains(@class, 'section_heading')][text()='Number of "
                                   "openings']/following-sibling::*[1]/text()").get()
        if vacancies:
            try:
                job_item['vacancies'] = int(vacancies.strip())
            except ValueError:
                job_item['vacancies'] = vacancies.strip()

        yield job_item
