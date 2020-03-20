import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class UotSpiderSpider(scrapy.Spider):
    name = 'uot_spider'
    allowed_domains = ['www.utas.edu.au', 'utas.edu.au']
    start_urls = ['https://www.utas.edu.au/courses/undergraduate',
                  'https://www.utas.edu.au/courses/postgraduate']

    def parse(self, response):
        courses = response.xpath("//div[@id='courseList']//div[@class='content-border']//a/@href").getall()
        courses = ["https://www.utas.edu.au/courses/university-college/courses/z2j-associate-degree-in-applied-science",
                   "https://www.utas.edu.au/courses/dvc-research/courses/s9a-doctor-of-philosophy-agriculture",
                   "https://www.utas.edu.au/courses/dvc-research/courses/d9c-doctor-of-philosophy-architecture-and-urban-environment"]

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of Tasmania"
        uidPrefix = "AU-UOT-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution

        course_item["courseName"] = response.xpath("//h1[@class='l-object-page-header--page-title']/text()").get()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        course_code = response.xpath("//h1[@class='l-object-page-header--page-title']/small/text()").get()
        course_code = re.findall("(?<=\()(.+?)(?=\))", course_code, re.DOTALL)
        if len(course_code) > 0:
            course_item["courseCode"] = course_code[0]

        course_item["overviewSummary"] = response.xpath("//div[@class='richtext richtext__medium']/div[@class='lede']/text()").get()
        overview = response.xpath("//div[@class='block block__gutter-md block__shadowed']/div[@class='block block__pad-lg']/div[@class='richtext richtext__medium']/*[not(contains(@class, 'lede'))]").getall()
        course_item["overview"] = "".join(overview)

        # course_item["whatLearn"] = response.xpath(
        #     "//div[@class='block block__gutter-md block__shadowed']//div[@role='tablist']//div[@class='richtext richtext__medium']").get()

        yield course_item