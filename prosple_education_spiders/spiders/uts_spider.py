# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def master(course_item):
    if "research" in course_item["courseName"].lower():
        return "12"

    else:
        return "11"

def bachelor(course_item):
    if "honour" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class UtsSpiderSpider(scrapy.Spider):
    name = 'uts_spider'
    # allowed_domains = ['https://www.uts.edu.au/future-students']
    start_urls = ['https://www.uts.edu.au/future-students/']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Technology, Sydney (UTS)"
    uidPrefix = "AU-UTS-"

    degrees = {
        "master": master,
        "bachelor": bachelor,
        "advanced master": "11",
        "executive master": "11",
        "juris doctor master": "11",
        "juris doctor graduate certificate": "7"
    }

    campus_map = {
        "blackfriars": "11789",
        "ultimo": "11717",
        "sydney": "820",
        "moore park": "819",
        "city campus": "818",
        "distance": "11724",
        "hong kong": "11723",
        "shanghai": "11720",
        "city campus (sydney)": "11719",
        "city": "11779"
    }

    holder = []

    def parse(self, response):
        categories = response.css("nav.content-menu--course-areas a::attr(href)").extract()
        for category in categories:
            yield response.follow(response.urljoin(category), callback=self.category_page)

    def category_page(self, response):
        sub_categories = response.css(".view-study-areas a::attr(href)").extract()
        for sub_category in sub_categories:
            yield response.follow(response.urljoin(sub_category), callback=self.sub_category_page)

    def sub_category_page(self, response):
        courses = response.css(".views-field a::attr(href)").extract()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(response.urljoin(course), callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_item["courseName"] = response.css("h1::text").extract_first()
        course_item["uid"] = self.uidPrefix + course_item["courseName"]

        course_item.set_sf_dt(self.degrees, ["\s"])

        overview = response.css(".read-more p::text").getall()
        if overview:
            overview = [cleanspace(x) for x in overview]
            course_item["overview"] = "\n".join(overview)
            course_item.set_summary(" ".join(overview))

        code = response.xpath("//dd[preceding-sibling::dt/text()='UTS']/span/text()").get()
        if code:
            course_item["courseCode"] = cleanspace(code)

        cricos = response.xpath("//dd[preceding-sibling::dt/text()='CRICOS']/text()").get()
        if cricos:
            course_item["cricosCode"] = cleanspace(cricos)
            course_item["internationalApps"] = 1

        careers = response.xpath("//p[preceding-sibling::h2/text()='Careers']/text()").getall()
        if careers:
            course_item["careerPathways"] = "\n".join([cleanspace(x) for x in careers])

        structure = response.xpath("//p[preceding-sibling::h2/text()='Course structure']/text()").getall()
        if structure:
            course_item["courseStructure"] = "\n".join([cleanspace(x) for x in structure])

        duration = response.xpath("//p[preceding-sibling::h3/text()='Course Duration']/text()").get()
        if duration:
            duration = cleanspace(duration)
            if duration != "":
                value = re.findall("[\d\.]+", duration)[0]
                if value:
                    if "year" in duration.lower():
                        course_item["teachingPeriod"] = 1
                        if "part" in duration.lower():
                            course_item["durationMinPart"] = value
                        elif "full" in duration.lower():
                            course_item["durationMinFull"] = value
                        else:
                            course_item.add_flag("duration", "Unknown duration pattern: "+duration)
                    else:
                        course_item.add_flag("teachingPeriod", "Unexpected period: "+duration)

                else:
                    course_item.add_flag("duration", "No duration value found: "+duration)

        campus = response.xpath("//p[preceding-sibling::h3/text()='Location']/text()").get()
        if campus:
            campus = [x.strip(" ") for x in campus.lower().split(",")]
            campus_holder = []
            mode_holder = []
            for item in campus:
                if "online" in item:
                    mode_holder.append("Online")

                if item in list(self.campus_map.keys()):
                    mode_holder.append("In person")
                    campus_holder.append(self.campus_map[item])
            course_item["campusNID"] = "|".join(list(set(campus_holder)))
            course_item["modeOfStudy"] = "|".join(list(set(mode_holder)))

        # print(self.holder)
        # if "flag" in course_item:
        #     # print(response.request.url)
        #     # print(course_item["flag"])
        yield course_item

