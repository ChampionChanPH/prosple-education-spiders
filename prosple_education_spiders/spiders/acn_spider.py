# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

class AcnSpiderSpider(scrapy.Spider):
    name = 'acn_spider'
    # allowed_domains = ['https://www.acn.edu.au/education/postgraduate-courses']
    start_urls = ['https://www.acn.edu.au/education/postgraduate-courses']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Australian College of Nursing (ACN)"
    uidPrefix = "AU-ACN-"

    download_delay = 5
    holder = {
        "duration": [],
        "mode": [],
        "months": []
    }

    duration_patterns = {
        "Year Part-time": {"field": "durationMinPart", "period": 1},
        "weeks": {"field": "durationMinFull", "period": 52}
    }

    def parse(self, response):
        yield SplashRequest(response.request.url, callback=self.postgrad_catalog, args={'wait': 10})

    def postgrad_catalog(self, response):
        courses = response.css(".standard-arrow a::attr(href)").getall()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(course, callback=self.course_parse, args={'wait': 10}, meta={"url":course})

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta["url"]

        course_item.set_course_name(response.css("div.uvc-sub-heading::text").get(), self.uidPrefix)
        course_item.set_sf_dt()

        cricos = response.css("h3 span::text").getall()
        # print(cricos)
        if cricos:
            for test in cricos:
                if "CRICOS" in test:
                    test = re.findall(":\s(\w+)", test)[0]
                    course_item["cricosCode"] = test
                    course_item["internationalApps"] = 1
                    course_item["internationalApplyURL"] = response.meta["url"]

        duration = response.xpath("//div[preceding-sibling::h4/text()='Duration']/div/p/text()").get()
        if duration:
            number = re.findall("[\d\.]+", duration)[0]
            pattern = re.findall("[\d\.]+\s(.*)$", duration)[0]
            if pattern in list(self.duration_patterns.keys()):
                course_item["teachingPeriod"] = self.duration_patterns[pattern]["period"]
                course_item[self.duration_patterns[pattern]["field"]] = number

            else:
                course_item.add_flag("teachingPeriod", "New duration pattern found: " + duration)

        mode = response.xpath("//div[preceding-sibling::h4/text()='Study mode']/div/p/text()").get()
        if mode:
            holder = []
            if "online" in mode.lower():
                holder.append("Online")

            if "face to face" in mode.lower():
                holder.append("In person")
                course_item["campusNID"] = "44194"

            course_item["modeOfStudy"] = "|".join(holder)

        months = response.xpath("//div[preceding-sibling::h4/text()='Intakes']/div/p/text()").get()

        if months:
            months = months.split(" ")
            months = convert_months(months)
            course_item["startMonths"] = months

        overview = response.xpath("//div[preceding-sibling::h2/text()='Course overview'][2]/div/p/text()").getall()
        if overview:
            course_item["overview"] = "<br>".join(overview)

        careerPathways = response.xpath("//div[preceding-sibling::h2/text()='Career outcomes'][2]/div/p/text()").getall()
        if careerPathways:
            course_item["careerPathways"] = "<br>".join(careerPathways)

        whatLearn = response.css("#outcomes .standard-arrow").get()
        if whatLearn:
            course_item["whatLearn"] = whatLearn

        entryRequirements = response.css("#requirements .standard-arrow").get()
        if entryRequirements:
            course_item["entryRequirements"] = entryRequirements

        courseStructure = response.xpath("//div[preceding-sibling::h2/text()='Units of study'][2]").get()
        if courseStructure:
            course_item["courseStructure"] = courseStructure

        yield course_item