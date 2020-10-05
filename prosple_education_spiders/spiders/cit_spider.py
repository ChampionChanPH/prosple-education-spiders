# by: Johnel Bacani
# started: Oct 5, 2020

from ..standard_libs import *


class CitSpiderSpider(scrapy.Spider):
    name = 'cit_spider'
    # allowed_domains = ['https://cit.edu.au/study/course_guide/az_courses']
    start_urls = ['https://cit.edu.au/study/course_guide/az_courses']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Canberra Institute of Technology"
    uidPrefix = "AU-CIT-"

    page_done = []

    def parse(self, response):
        courses = response.css("#content_div_8251 p a::attr(href)").getall()
        for course in courses:
            if "result_page" in course: #course actually conatins a page url in this case
                if "result_page" in response.request.url:
                    pass
                else:
                    if course not in self.page_done:
                        self.page_done.append(course)
                        yield response.follow(course, callback=self.parse)

            else:
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

        name = response.xpath("//div[contains(@class,'information-box')]/div/span").get()
        if name:
            name = cleanspace(re.sub("<.*?>", "", name))
            print(name.split(" ")[-1])
            if re.match("\d", name.split(" ")[-1]):

                print(name.split(" ")[-1])
            course_item.set_course_name(name, self.uidPrefix)

        else:
            course_item.add_flag("courseName", "No course name found.")

        # yield course_item