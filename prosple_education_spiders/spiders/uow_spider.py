# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *
import ast

def bachelor(course_item):
    if "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class UowSpiderSpider(scrapy.Spider):
    name = 'uow_spider'
    # allowed_domains = ['https://coursefinder.uow.edu.au/search-results/index.html']
    start_urls = ['https://coursefinder.uow.edu.au/index.html']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "http://coursefinder.uow.edu.au/information/index.html?course=master-international-relations-2",
        "http://coursefinder.uow.edu.au/undergrad/index.html",
        "http://coursefinder.uow.edu.au/information/index.html?course=bachelor-social-science-public-health"
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "University of Wollongong (UOW)"
    uidPrefix = "AU-UOW-"

    holder = []
    campus_map = {
        'Southern Sydney': "837",
        'Batemans Bay': "836",
        'Southern Highlands': "834",
        'Bega': "835",
        'Shoalhaven': "833",
        # 'UOW Online Wollongong',
        'Sydney': "838",
        'Innovation Campus': "831",
        'South Western Sydney': "832",
        'Wollongong': "830",
    }


    #['Southern Sydney', 'Batemans Bay', 'Southern Highlands', 'Bega', 'Shoalhaven', 'UOW Online Wollongong', 'Sydney', 'Innovation Campus', 'South Western Sydney', 'Wollongong']

    degrees = {
        "master": "11",
        "bachelor": bachelor,
    }
    # init_lua = """
    # function main(splash, args)
    #   local get_div_count = splash:jsfunc([[
    #   function () {
    #     var courses = [];
    #     var body = document.body;
    #     courses.concat(body.getElementsByTagName('li.next'));
    #   }
    #   ]])
    #   splash:go(args.url)
    #
    #   return ("There are %s DIVs in %s"):format(
    #     get_div_count(), args.url)
    # end
    # function main(splash, args)
    #   assert(splash:go(args.url))
    #   assert(splash:wait(10))
    #   local test_list = 0
    #   return {
    #     html = splash:html(),
    #     test = test_list
    #   }
    # end
    # """

    # def start_requests(self):
    #     for url in self.start_urls:
    #         return [scrapy.FormRequest(url, callback=self.parse, errback=self.err_parse)]

    def parse(self, response):
        yield SplashRequest(self.start_urls[0], callback=self.splash_index, args={'wait': 2}, meta={"url": self.start_urls[0]})
        # yield SplashRequest(self.start_urls[0], self.splash_index, endpoint='execute', args={'lua_source': self.init_lua, 'url': self.start_urls[0]})

    # def err_parse(self, response):
    #     # yield SplashRequest(self.start_urls[0], callback=self.splash_index, args={'wait': 10})
    #     yield SplashRequest(self.start_urls[0], self.splash_index, endpoint='execute', args={'lua_source': self.init_lua, 'url': self.start_urls[0]})

    def splash_index(self, response):
        categories = response.css("ul.study-options li a::attr(href)").getall()
        categories = [response.meta["url"].replace("/index.html","") + x for x in categories]
        for category in categories:
            yield response.follow(category, callback=self.list_parse)

    def list_parse(self, response):
        undergrad_courses = response.css("div.undergraduate li a::attr(href)").getall()
        for course in undergrad_courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(course, callback=self.course_parse, args={"wait": 2}, meta={"level": "1", "url": course})

        postgrad_courses = response.css("div.postgraduate li a::attr(href)").getall()
        for course in postgrad_courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(course, callback=self.course_parse, args={"wait": 2}, meta={"level": "2", "url": course})

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution
        # course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)
        else:
            return

        course_item.set_sf_dt(self.degrees)

        overview = response.css("div#course-summary p""text").get()
        if overview:
            course_item["overview"] = overview
            course_item.set_summary(overview)

        what_learn = response.xpath("//p[strong/text()='What you will study']/text()").get()
        if what_learn:
            course_item["whatLearn"] = what_learn

        campus = response.xpath("//p[preceding-sibling::p/text()='Campus']/text()").get()
        if campus:
            campus = [x.strip() for x in cleanspace(campus).split(",")]
            campuses = map_convert(self.campus_map, campus)
            course_item["campusNID"] = "|".join(campuses["converted"])


        course_code = response.xpath("//p[preceding-sibling::p/text()='Course Code']/text()").get()
        if course_code:
            course_code = cleanspace(course_code)
            course_item["courseCode"] = course_code

        cricos_code = response.xpath("//p[preceding-sibling::p/text()='Cricos']/text()").get()
        if cricos_code:
            cricos_code = cleanspace(cricos_code)
            course_item["courseCode"] = cricos_code

        mode = response.xpath("//p[preceding-sibling::p/text()='Delivery']/text()").get()
        if mode:
            holder = []
            mode = [x.strip() for x in cleanspace(mode).split(",")]
            if "On Campus" in mode:
                holder.append("In person")
            if "Flexible" in mode:
                holder.append("In person")
                holder.append("Online")
            if "Distance" in mode:
                holder.append("Online")
            course_item["modeOfStudy"] = "|".join(list(set(holder)))

        duration = response.xpath("//p[preceding-sibling::p/text()='Duration']/text()").get()
        if duration:
            if " or " in duration:
                durations = cleanspace(duration.lower()).split(" or ")
            else:
                durations = cleanspace(duration.lower()).split(";")
            # print(durations)
            if durations:
                for i in durations:
                    value = re.findall("[\d\.]+", i)
                    if value:
                        value = value[0]

                        if "full" in i:
                            field = "durationMinFull"
                        elif "part" in i:
                            field = "durationMinPart"
                        else:
                            course_item.add_flag("duration", "Can't tell which duration: " + i)
                            break

                        course_item[field] = value

                        period = get_period(re.findall("\d\s?(\w+)", i)[0])
                        if period != 0:
                            course_item["teachingPeriod"] = period
                        else:
                            course_item.add_flag("teachingPeriod", "Can't determine teaching period: " + i)

        yield course_item