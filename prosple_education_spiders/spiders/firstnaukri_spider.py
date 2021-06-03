# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


class FirstnaukriSpiderSpider(scrapy.Spider):
    name = 'firstnaukri_spider'
    start_urls = ['https://www.firstnaukri.com/fnJobSearch/search-1?sortBy=&jobType=&rId=&qp=&ql=&course=&qcourse=']

    def parse(self, response):
        jobs = response.xpath("//div[@class='groupTupples']//a[@class='header']/@href").getall()
        yield from response.follow_all(jobs, callback=self.job_parse)

        next_page = response.xpath("//a[@class='next']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def job_parse(self, response):
        job_item = Opportunity()

        job_item["source_url"] = response.request.url
        job_item["time_zone"] = "Asia/Kolkata"
        job_item["group"] = 41
        job_item["canonical_group"] = "GradIndia"
        job_item["application_link"] = response.request.url

        job_name = response.xpath("//*[@class='jhTitle elp']/text()").get()
        if job_name:
            job_item["opportunity_name"] = job_name.strip()

        employer_name = response.xpath("//*[@class='w765 compName elp']/text()").get()
        if employer_name:
            job_item["employer_name"] = employer_name.strip()

        overview = response.xpath("//div[@class='tableStr']/*[last()]/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            job_item.set_summary(' '.join(summary))
            job_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        employer_profile = response.xpath("//*[text()='Company Profile']/following-sibling::*").getall()
        if employer_profile:
            job_item["employer_description"] = strip_tags(''.join(employer_profile), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        no_of_vacancies = response.xpath("//span[@class='jdCell' and text()='Openings']/following-sibling::*["
                                         "@class='jdCell2']/text()").get()
        if no_of_vacancies:
            try:
                job_item["no_of_vacancies"] = int(no_of_vacancies)
            except ValueError:
                job_item["no_of_vacancies"] = no_of_vacancies

        industry_sector = response.xpath("//span[@class='jdCell' and text()='Industry Type']/following-sibling::*["
                                         "@class='jdCell2']/text()").get()
        if not industry_sector:
            industry_sector = response.xpath("//span[@class='jdCell' and text()='Functional "
                                             "Area']/following-sibling::*[@class='jdCell2']/text()").get()
        if industry_sector:
            job_item['industry_sector'] = industry_sector.strip()

        employer_url = response.xpath("//span[@class='jdCell' and text()='Website']/following-sibling::*[contains("
                                      "@class, 'jdCell2')]/a/@href").get()
        if employer_url:
            job_item['employer_url'] = employer_url.strip()

        salary = response.xpath("//*[@class='icon-inr']/following-sibling::*/text()").get()
        if salary:
            job_item["salary_description"] = salary.strip()

        location = response.xpath("//*[@class='icon-location']/following-sibling::*/text()").get()
        if location:
            job_item["location"] = location.strip()

        yield job_item
