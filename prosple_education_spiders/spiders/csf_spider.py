import scrapy


class CsfSpiderSpider(scrapy.Spider):
    name = 'csf_spider'
    allowed_domains = ['a']
    start_urls = ['http://a/']

    def parse(self, response):
        pass
