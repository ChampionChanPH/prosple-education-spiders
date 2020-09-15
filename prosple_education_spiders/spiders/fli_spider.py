# by: Johnel Bacani

from ..standard_libs import *

class FliSpiderSpider(scrapy.Spider):
    name = 'fli_spider'
    # allowed_domains = ['www.flinders.edu.au/study']
    start_urls = [
        'https://www.flinders.edu.au/study'
        # 'https://www.flinders.edu.au/study/business',
        # 'https://www.flinders.edu.au/study/creative-arts-media',
        # 'https://www.flinders.edu.au/study/criminology',
        # 'https://www.flinders.edu.au/study/defence-national-security',
        # 'https://www.flinders.edu.au/study/education',
        # 'https://www.flinders.edu.au/study/engineering',
        # 'https://www.flinders.edu.au/study/environment',
        # 'https://www.flinders.edu.au/study/health',
        # 'https://www.flinders.edu.au/study/humanities-social-sciences',
        # 'https://www.flinders.edu.au/study/information-technology',
        # 'https://www.flinders.edu.au/study/international-relations-political-science',
        # 'https://www.flinders.edu.au/study/languages-culture',
        # 'https://www.flinders.edu.au/study/law',
        # 'https://www.flinders.edu.au/study/medicine',
        # 'https://www.flinders.edu.au/study/nursing-midwifery',
        # 'https://www.flinders.edu.au/study/psychology',
        # 'https://www.flinders.edu.au/study/science',
        # 'https://www.flinders.edu.au/study/social-work',
        # 'https://www.flinders.edu.au/study/sport'
    ]

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Flinders University"
    uidPrefix = "AU-FLI-"

    def parse(self, response):
        categories = response.xpath("//a[@name='courses']/following-sibling::div[contains(@class, 'container_fullwidth')]//a[contains(@class, 'list-group-item')]/@href").getall()
        categories = list(set(categories))
        for category in categories:
            if category != '#contact':
                yield response.follow(category, callback=self.category_parse)


    def category_parse(self, response):
        courses = response.css("ul.course_list a::attr(href)").getall()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        yield course_item

