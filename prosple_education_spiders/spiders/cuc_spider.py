import scrapy


class CucSpiderSpider(scrapy.Spider):
    name = 'cuc_spider'
    allowed_domains = ['a']
    start_urls = ['http://a/']

    def parse(self, response):
        pass
