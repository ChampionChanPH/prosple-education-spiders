import scrapy


class NeitSpiderSpider(scrapy.Spider):
    name = 'neit_spider'
    allowed_domains = ['a']
    start_urls = ['http://a/']

    def parse(self, response):
        pass
