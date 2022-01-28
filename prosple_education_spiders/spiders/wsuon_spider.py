import scrapy


class WsuonSpiderSpider(scrapy.Spider):
    name = 'wsuon_spider'
    allowed_domains = ['online.westernsydney.edu.au']
    start_urls = ['https://online.westernsydney.edu.au/online-courses//']

    def parse(self, response):
        pass
