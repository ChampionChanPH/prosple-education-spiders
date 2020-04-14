import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class UoaSpiderSpider(scrapy.Spider):
    name = 'uoa_spider'
    allowed_domains = ['www.adelaide.edu.au', 'adelaide.edu.au']
    start_urls = ['https://www.adelaide.edu.au/degree-finder/?v__s=&m=view&dsn=program.source_program&adv_avail_comm'
                  '=1&adv_acad_career=0&adv_degree_type=0&adv_atar=0&year=2020&adv_subject=0&adv_career=0&adv_campus'
                  '=0&adv_mid_year_entry=0']

    def parse(self, response):
        courses = response.xpath("//div[@class='c-table']//a/@href").getall()

        courses = [
            "https://www.adelaide.edu.au/degree-finder/2020/mml_mmaclearn.html",
            "https://www.adelaide.edu.au/degree-finder/2020/drcd_drclinden.html",
            "https://www.adelaide.edu.au/degree-finder/2020/mmesc_mmesc.html"
        ]

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of Adelaide"
        uidPrefix = "AU-UOA-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h2/text()").get()
        course_item["courseName"] = course_name.strip()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        yield course_item
