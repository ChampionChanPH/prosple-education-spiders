# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class UoSpiderSpider(scrapy.Spider):
    name = 'uo_spider'
    # allowed_domains = ['https://www.otago.ac.nz/courses/qualifications/apply/index.html']
    start_urls = ['https://www.otago.ac.nz/courses/qualifications/apply/index.html']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Otago"
    uidPrefix = "NZ-UO-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "diploma for graduates": "8"
    }

    def parse(self, response):
        courses = response.css("#content ul a::attr(href)").getall()
        # courses = ["https://www.otago.ac.nz/courses/qualifications/mspdm.html"]
        for course in [x for x in courses if x[0] != "#" and "/subjects/" not in x]:
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
            course_item["campusNID"] = "48009"

            name = response.css(".titleinner h1::text").get()
            if name:
                course_item.set_course_name(cleanspace(name), self.uidPrefix)

            course_item.set_sf_dt(self.degrees, ["and"])

            # Overide canonical group
            course_item["group"] = 2
            course_item["canonicalGroup"] = "GradNewZealand"

            code = re.findall("\((.*?)\)", name)
            if code:
                course_item["courseCode"] = code[0]

            nav = response.css("ul.pagesubnav li a::attr(href)").getall()
            if nav:
                nav = [x.replace("#", "") for x in nav]
                for i in range(len(nav)-1):
                    section = response.xpath("//*[preceding-sibling::p/a[@name='" + nav[i] + "']][following-sibling::p/a[@name='" + nav[i+1] + "']]")
                    header = section.css("h2::text").get()

                    if header == "Overview":
                        # print(section.getall())
                        overview = section.getall()
                        # print(overview)
                        if overview:
                            holder = []
                            for element in overview:
                                if 'class="topofpage"' in element:
                                    break
                                elif "<h2>" in element:
                                    pass
                                else:
                                    holder.append(re.sub("<.*?>", "", element))
                                    # holder.append(element)
                            course_item["overview"] = " ".join([cleanspace(x) for x in holder])
                            course_item.set_summary(course_item["overview"])

            # if "flag" in course_item:
            yield course_item
