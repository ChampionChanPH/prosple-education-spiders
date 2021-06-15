from ..standard_libs import *
from ..scratch_file import *
import requests


class Forum(scrapy.Item):
    forum_title = scrapy.Field()
    forum_link = scrapy.Field()
    user_id = scrapy.Field()
    username = scrapy.Field()
    post_date = scrapy.Field()
    comment = scrapy.Field()


class WhirlpoolSpiderSpider(scrapy.Spider):
    name = 'whirlpool_spider'
    start_urls = ['https://forums.whirlpool.net.au/forum/136?&p=1']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    def parse(self, response):
        # for num in range(1, 11):
        for num in range(1, 2):
            url = f"https://forums.whirlpool.net.au/forum/136?&p={num}"

            yield response.follow(url, callback=self.sub_parse)

    def sub_parse(self, response):
        threads = response.xpath("//tr[contains(@class, 'thread')]")

        for item in threads:
            forum_title = item.xpath(".//a[@class='title']/text()").getall()
            forum_link = item.xpath(".//a[@class='title']/@href").getall()

            for title, url in zip(forum_title, forum_link):
                yield response.follow(url, callback=self.pagination_parse, meta={"title": title,
                                                                              "url": url})

    def pagination_parse(self, response):
        forum_title = response.meta['title']
        forum_link = response.meta['url']
        num = 1
        start_url = response.request.url

        while True:
            url = f"{start_url}?p={num}"

            r = requests.get(url)
            if r.status_code >= 300:
                break
            else:
                yield response.follow(url, callback=self.comment_parse, meta={"title": forum_title,
                                                                              "url": forum_link})
            num += 1

    def comment_parse(self, response):
        forum = Forum()

        comments = response.xpath("//div[@id='replylist']/div[contains(@id, 'rr')]")

        for item in comments:
            forum['forum_title'] = response.meta['title']
            forum['forum_link'] = response.meta['url']

            forum['username'] = item.xpath(".//div[contains(@class, 'reply ')]//span[@class='bu_name']/text()").get().strip()
            forum['user_id'] = item.xpath(".//div[contains(@class, 'reply ')]//span[@class='userid']/text()").get().strip()
            forum['user_group'] = item.xpath(".//div[contains(@class, 'reply ')]//div[@class='usergroup']/text()").get().strip()

            post_date = item.xpath(".//div[contains(@class, 'reply ')]//div[@class='usergroup']/text()").getall()
            if post_date:
                post_date = ''.join(post_date).strip()
                forum['post_date'] = post_date

            comment = item.xpath(".//div[contains(@class, 'reply ')]/div[@class='replytext bodytext']/*").getall()
            if comment:
                forum['comment'] = strip_tags(''.join(comment), remove_all_tags=False, remove_hyperlinks=True)

            yield forum
