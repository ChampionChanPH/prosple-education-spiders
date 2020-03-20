import scrapy
import re
from ..items import Course
from datetime import date


class CuuSpider(scrapy.Spider):
    name = 'cuu_spider'
    allowed_domains = ['www.acu.edu.au', 'study.curtin.edu.au', 'search.curtin.edu.au']
    start_urls = ['https://study.curtin.edu.au/search/?pageno=1']
    categories = []
    campuses = ["Perth", "Mauritius", "Malaysia", "Singapore", "Perth City", "Kalgoorlie", "Bentley",
                "Open Universities Australia"]

    def parse(self, response):
        self.categories.extend(response.xpath("//div[@class='search-results__card-container']//a/@href").getall())

        next_page = response.xpath("//a[@class='search-pagination__next']/@href").get()

        self.categories = ['https://study.curtin.edu.au/offering/course-ug-bachelor-of-science-nursing--b-nursv2/']

        # if next_page is not None:
        #     yield response.follow(next_page, callback=self.parse)

        for category in self.categories:
            yield response.follow(category, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url

        title = response.xpath("//title/text()").get()
        course_name = re.findall(r'.+?(?= - Study)', title, re.DOTALL)
        course_item['courseName'] = course_name[0].replace(",", " /")

        course_details = response.xpath("string(//dl[@class='smaller'])").get()
        course_details = re.findall(r'[0-9]+\s[year|years|month|months].+?full.time', course_details,
                                                re.DOTALL | re.MULTILINE)
        if course_details is not None:
            course_item['durationRaw'] = course_details

        location = response.xpath("string(//section[contains(@class, 'location')])").get()
        study_mode_container = []

        campus_container = []
        for campus in self.campuses:
            campus_container.extend(re.findall(campus, location, re.MULTILINE | re.IGNORECASE))
        if re.search(r'on campus', location, re.IGNORECASE):
            study_mode_container.append('In Person')
        if re.search('online', location, re.IGNORECASE):
            campus_container.append('Open Universities Australia')
            study_mode_container.append('Online')
        campus_container = set(campus_container)
        course_item['campusNID'] = ", ".join(campus_container)
        course_item['modeOfStudy'] = '|'.join(study_mode_container)

        course_item['overview'] = response.xpath("//div[contains(@class, 'outline__content') and contains("
                                                  "@class, 'content')]").getall()
        course_item['entryRequirements'] = response.xpath("//section[contains(@class, 'admission-criteria')]")\
            .getall()
        course_item['howToApply'] = response.xpath("//section[contains(@class, 'how-to-apply')]").getall()

        yield course_item
