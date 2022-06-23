# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by Christian Anasco

from ..standard_libs import *
from ..scratch_file import strip_tags


def research_coursework(course_item):
    if re.search("research", course_item["courseName"], re.I):
        return "12"
    else:
        return "11"


def bachelor_honours(course_item):
    if re.search("honours", course_item["courseName"], re.I):
        return "3"
    else:
        return "2"


def get_total(field_to_use, field_to_update, course_item):
    if "durationMinFull" in course_item and "teachingPeriod" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])
        if course_item["teachingPeriod"] == 12:
            if float(course_item["durationMinFull"]) < 12:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"]) \
                    / 12
        if course_item["teachingPeriod"] == 52:
            if float(course_item["durationMinFull"]) < 52:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"]) \
                    / 52


class UowSpiderSpider(scrapy.Spider):
    name = 'uow_spider'
    # allowed_domains = ['https://coursefinder.uow.edu.au/search-results/index.html']
    start_urls = [
        'https://www.uow.edu.au/study/accounting-finance-economics/',
        'https://www.uow.edu.au/study/business-marketing-management/',
        'https://www.uow.edu.au/study/law/',
        'https://www.uow.edu.au/study/communications-media/',
        'https://www.uow.edu.au/study/computer-science-information-technology/',
        'https://www.uow.edu.au/study/creative-arts/',
        'https://www.uow.edu.au/study/education/',
        'https://www.uow.edu.au/study/engineering/',
        'https://www.uow.edu.au/study/environmental-biological-sciences/',
        'https://www.uow.edu.au/study/health/',
        'https://www.uow.edu.au/study/humanities/',
        'https://www.uow.edu.au/study/literature-language/',
        'https://www.uow.edu.au/study/mathematics-physics-chemistry/',
        'https://www.uow.edu.au/study/medical-science/',
        'https://www.uow.edu.au/study/nursing/',
        'https://www.uow.edu.au/study/psychology-human-behaviour/',
        'https://www.uow.edu.au/study/social-sciences-advocacy/',
    ]

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "http://coursefinder.uow.edu.au/information/index.html?course=master-international-relations-2",
        "http://coursefinder.uow.edu.au/undergrad/index.html",
        "http://coursefinder.uow.edu.au/information/index.html?course=bachelor-social-science-public-health",
        "http://coursefinder.uow.edu.au/two-masters-two-years/index.html",
        "http://coursefinder.uow.edu.au/information/index.html?course=bachelor-mathematics-education-deans-scholar",
        "http://coursefinder.uow.edu.au/creative-performing-arts/ssNODELINK/1674",
        "http://coursefinder.uow.edu.au/double-degrees/index.html",
        "http://coursefinder.uow.edu.au/double-degrees/communications-media/index.html",
        "http://coursefinder.uow.edu.au/double-degrees/engineering/index.html",
        "http://coursefinder.uow.edu.au/double-degrees/science/index.html",
        "http://coursefinder.uow.edu.au/double-degrees/mathematics-statistics/index.html",
        "http://coursefinder.uow.edu.au/information/ssLINK/H20008090",
        "http://coursefinder.uow.edu.au/undergrad/index.html",
        "http://coursefinder.uow.edu.au/double-degrees/business/index.html",
        "https://coursefinder.uow.edu.au/information/index.html?course=master-international-relations-2",
        "https://coursefinder.uow.edu.au/undergrad/index.html",
        "https://coursefinder.uow.edu.au/information/index.html?course=bachelor-social-science-public-health",
        "https://coursefinder.uow.edu.au/two-masters-two-years/index.html",
        "https://coursefinder.uow.edu.au/information/index.html?course=bachelor-mathematics-education-deans-scholar",
        "https://coursefinder.uow.edu.au/creative-performing-arts/ssNODELINK/1674",
        "https://coursefinder.uow.edu.au/double-degrees/index.html",
        "https://coursefinder.uow.edu.au/double-degrees/communications-media/index.html",
        "https://coursefinder.uow.edu.au/double-degrees/engineering/index.html",
        "https://coursefinder.uow.edu.au/double-degrees/science/index.html",
        "https://coursefinder.uow.edu.au/double-degrees/mathematics-statistics/index.html",
        "https://coursefinder.uow.edu.au/information/ssLINK/H20008090",
        "https://coursefinder.uow.edu.au/undergrad/index.html",
        "https://coursefinder.uow.edu.au/double-degrees/business/index.html",
    ]
    scraped_urls = []
    superlist_urls = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"

    institution = "University of Wollongong (UOW)"
    uidPrefix = "AU-UOW-"

    holder = []
    campuses = {
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
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "undergraduate certificate": "4",
        "certificate iv": "4",
        "certificate iii": "4",
        "certificate ii": "4",
        "certificate i": "4",
        "certificate": "4",
        "diploma": "5",
        "advanced diploma": "5",
        "tafe advanced diploma": "5",
        "undergraduate diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    teaching_periods = {
        "year": 1,
        "semester": 2,
        "trimester": 3,
        "quarter": 4,
        "month": 12,
        "week": 52,
        "day": 365
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

    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath(
            "//div[contains(@class, 'uw-tabs-content')]//div[@class='cell large-auto']/ul//a/@href").getall()

        for item in courses:
            if re.search("coursefinder.uow.edu.au", item) and item not in self.blacklist_urls:
                yield SplashRequest(item, callback=self.course_parse, args={'wait': 5}, meta={'url': item})

        # yield SplashRequest(self.start_urls[0], callback=self.splash_index, args={'wait': 2}, meta={"url": self.start_urls[0]})
        # yield SplashRequest(self.start_urls[0], self.splash_index, endpoint='execute', args={'lua_source': self.init_lua, 'url': self.start_urls[0]})

    # def err_parse(self, response):
    #     # yield SplashRequest(self.start_urls[0], callback=self.splash_index, args={'wait': 10})
    #     yield SplashRequest(self.start_urls[0], self.splash_index, endpoint='execute', args={'lua_source': self.init_lua, 'url': self.start_urls[0]})

    # def splash_index(self, response):
    #     categories = response.css("ul.study-options li a::attr(href)").getall()
    #     categories = [response.meta["url"].replace(
    #         "/index.html", "") + x for x in categories]
    #     for category in categories:
    #         yield response.follow(category, callback=self.list_parse)

    # def list_parse(self, response):
    #     undergrad_courses = response.css(
    #         "div.undergraduate li a::attr(href)").getall()
    #     for course in undergrad_courses:
    #         if course not in self.blacklist_urls and course not in self.scraped_urls:
    #             if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
    #                 self.scraped_urls.append(course)
    #                 yield SplashRequest(course, callback=self.course_parse, args={"wait": 2}, meta={"level": "1", "url": course})

    #     postgrad_courses = response.css(
    #         "div.postgraduate li a::attr(href)").getall()
    #     for course in postgrad_courses:
    #         if course not in self.blacklist_urls and course not in self.scraped_urls:
    #             if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
    #                 self.scraped_urls.append(course)
    #                 yield SplashRequest(course, callback=self.course_parse, args={"wait": 2}, meta={"level": "2", "url": course})

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.meta["url"]
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item["domesticApplyURL"] = response.meta["url"]

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name, self.uidPrefix)

        overview = response.xpath(
            "//h2[contains(@class, 'section-title') and text()='Course summary']/following-sibling::*/*").getall()
        holder = []
        if overview:
            overview = [x for x in overview if strip_tags(x) != ""]
            for item in overview:
                if re.search("^<p><strong>", item):
                    break
                else:
                    holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        # what_learn = response.xpath(
        #     "//p[strong/text()='What you will study']/text()").get()
        # if what_learn:
        #     course_item["whatLearn"] = what_learn

        career = response.xpath(
            "//*[contains(@class, 'section-title') and text()='Career opportunities']/following-sibling::ul").getall()
        if career:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        start = response.xpath(
            "//p[contains(text(), 'Orientation:')]").getall()
        holder = []
        for item in start:
            split_text = item.split("Session:")
            if len(split_text) > 1:
                holder.append(split_text[0])
            elif len(split_text) == 1:
                holder.append(split_text)
        start_holder = []
        if holder:
            start = "".join(holder)
            for month in self.months:
                if re.search(month, start, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        location = response.xpath(
            "//p[@class='label' and text()='Campus']/following-sibling::*/text()").get()
        campus_holder = []
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)

        atar = response.xpath(
            "//p[@class='label' and a/text()='ATAR-SR ']/following-sibling::*/text()").get()
        if atar:
            atar = re.findall("\d+\.?\d*", atar)
            if atar:
                course_item["guaranteedEntryScore"] = float(atar[0])

        course_code = response.xpath(
            "//p[@class='label' and text()='Course Code']/following-sibling::*/text()").get()
        if course_code:
            course_item["courseCode"] = strip_tags(course_code)

        cricos = response.xpath(
            "//p[@class='label' and text()='Cricos']/following-sibling::*").getall()
        if cricos:
            cricos = "".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.meta["url"]

        study = duration = response.xpath(
            "//p[@class='label' and text()='Delivery']/following-sibling::*").getall()
        holder = set()
        if study:
            study = "".join(study)
            if re.search("campus", study, re.I | re.M):
                holder.add("In Person")
            if re.search("distance", study, re.I | re.M) or re.search("online", study, re.I | re.M):
                holder.add("Online")
        if holder:
            course_item["modeOfStudy"] = "|".join(holder)

        duration = response.xpath(
            "//p[@class='label' and text()='Duration']/following-sibling::*").getall()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
                duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                        / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/', '-'], type_delims=['of', 'in', 'by', 'for'])

        if course_item["courseName"] not in ["Course Finder", "Start your journey", "Two Masters in"]:
            yield course_item
