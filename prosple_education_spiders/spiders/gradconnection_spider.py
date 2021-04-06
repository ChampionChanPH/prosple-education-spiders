from ..standard_libs import *


class Employer(scrapy.Item):
    employer_name = scrapy.Field()
    profile_link = scrapy.Field()


class GradconnectionSpiderSpider(scrapy.Spider):
    name = 'gradconnection_spider'
    start_urls = [
        'https://ph.gradconnection.com/employers/?page=1',
        'https://ph.gradconnection.com/employers/?page=2',
        'https://ph.gradconnection.com/employers/?page=3',
        'https://ph.gradconnection.com/employers/?page=4',
        'https://ph.gradconnection.com/employers/?page=5',
        'https://ph.gradconnection.com/employers/?page=6',
        'https://ph.gradconnection.com/employers/?page=7',
        'https://ph.gradconnection.com/employers/?page=8',
    ]

    def parse(self, response):
        employers = response.xpath("//a[@class='title-link']/@href").getall()

        for item in employers:
            yield response.follow(item, callback=self.employer_parse)

    def employer_parse(self, response):
        employer_item = Employer()

        employer_item['profile_link'] = response.request.url
        name = response.xpath("//p[@class='employers-panel-title']/text()").get()
        if name:
            employer_item['employer_name'] = name.strip()

        yield employer_item
