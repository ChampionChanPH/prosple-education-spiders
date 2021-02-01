from ..standard_libs import *


class ReviewFields(scrapy.Item):
    companyName = scrapy.Field()
    reviewScore = scrapy.Field()
    reviewCount = scrapy.Field()
    sourceURL = scrapy.Field()


class GlassSpiderSpider(scrapy.Spider):
    name = 'glass_spider'
    download_delay = 5.0
    start_urls = ['https://www.glassdoor.com/Reviews/Two-Degrees-Mobile-New-Zealand-Reviews-EI_IE580176.0,18_IL.19,'
                  '30_IN186.htm?filter.iso3Language=eng&filter.employmentStatus=REGULAR&filter.employmentStatus'
                  '=PART_TIME']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.review_parse, args={'wait': 20})

    def sub_parse(self, response):
        reviews = response.xpath("//div[@data-automation='CompanyDetails']//a/@href").getall()

        for item in reviews:
            yield response.follow(item, callback=self.review_parse)

    def review_parse(self, response):
        review_item = ReviewFields()

        review_item['companyName'] = response.xpath("//span[@id='DivisionsDropdownComponent']").getall()
        review_item['reviewCount'] = response.xpath("//h2[@data-test='overallReviewCount']").getall()
        review_item['reviewScore'] = response.xpath("//div[contains(@class, 'v2__EIReviewsRatingsStylesV2__ratingNum']").getall()

        yield review_item
