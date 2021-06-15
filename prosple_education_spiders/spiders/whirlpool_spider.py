from ..standard_libs import *
from ..scratch_file import *
import requests


class Forum(scrapy.Item):
    forum_title = scrapy.Field()
    forum_link = scrapy.Field()
    user_id = scrapy.Field()
    user_group = scrapy.Field()
    username = scrapy.Field()
    post_date = scrapy.Field()
    comment = scrapy.Field()


class WhirlpoolSpiderSpider(scrapy.Spider):
    name = 'whirlpool_spider'
    start_urls = ['https://forums.whirlpool.net.au/forum/136']
    download_delay = 1

    def parse(self, response):
        for num in range(1, 11):
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
            forum['forum_link'] = f"https://forums.whirlpool.net.au{response.meta['url']}"

            user_id = item.xpath(
                ".//div[contains(@class, 'reply ')]//span[@class='userid']/text()").get()
            if user_id:
                forum['user_id'] = user_id.strip()

            user_group = item.xpath(
                ".//div[contains(@class, 'reply ')]//div[@class='usergroup']/text()").get()
            if user_group:
                forum['user_group'] = user_group.strip()

            username = item.xpath(
                ".//div[contains(@class, 'reply ')]//span[@class='bu_name']/text()").get()
            if username:
                forum['username'] = username.strip()

            post_date = item.xpath(".//div[contains(@class, 'reply ')]//div[@class='date']/a[text("
                                   ")='posted']/following-sibling::text()").get()
            if post_date:
                forum['post_date'] = post_date.strip()

            comment = item.xpath(".//div[contains(@class, 'reply ')]/div[@class='replytext bodytext']/*").getall()
            if comment:
                forum['comment'] = strip_tags(''.join(comment), remove_all_tags=False, remove_hyperlinks=True)

            yield forum
