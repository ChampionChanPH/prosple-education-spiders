# by: Johnel Bacani

from ..standard_libs import *

def bachelor(course_item):
    if "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class JcuSpiderSpider(scrapy.Spider):
    name = 'jcu_spider'
    # allowed_domains = ['https://www.jcu.edu.au/courses-and-study/study-areas']
    start_urls = ['https://www.jcu.edu.au/courses/study']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "James Cook University (JCU)"
    uidPrefix = "AU-JCU-"

    holder = []
    counter = 0
    campus_map = {
        "mount isa": "53598",
        "mackay": "53604",
        "townsville": "620",
        "singapore": "621",
        "brisbane": "619",
        "cairns": "618"
    }

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "online graduate diploma": "8",
        "online graduate certificate": "7",
    }

    def parse(self, response):
        categories = response.css("li.jcu-v1__ct__link-list__item a::attr(href)").getall()
        for category in categories:
            yield response.follow(category, callback=self.category_parse)

    def category_parse(self, response):
        courses = response.css("a.jcu-v1__course-table--name__link::attr(href)").getall()
        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    if "online.jcu.edu.au" in course:
                        pass
                        # yield response.follow(course, callback=self.online_course_parse)
                    else:
                        yield response.follow(course, callback=self.course_parse)

    # def online_course_parse(self, response):
        # course_item = Course()
        # course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        # course_item["sourceURL"] = response.request.url
        # course_item["published"] = 1
        # course_item["institution"] = self.institution
        #
        # name = response.css("figure h1::text").get()
        # if name:
        #     course_item.set_course_name(name, self.uidPrefix)
        # course_item.set_sf_dt(self.degrees, degree_delims=["-", ","])
        # course_item["modeOfStudy"] = "Online"
        #
        # overview = response.css(".stuckright p::text").getall()
        # if overview:
        #     course_item["overview"] = "\n".join(overview[:-1])
        #     course_item.set_summary(" ".join(overview[:-1]))
        #
        # start = response.css(".views-field-field-course-study-periods div::text").get()
        # if start:
        #     course_item["startMonths"] = "|".join(convert_months([cleanspace(x) for x in start.split(",")]))
        #
        # duration = response.css(".views-field-field-course-duration div::text").get()
        # if duration:
        #     value = re.findall("[\d\.]+", duration)
        #     if value:
        #         if "part-time" in duration:
        #             course_item["durationMinPart"] = value[0]
        #         else:
        #             course_item["durationMinFull"] = value[0]
        #     if "month" in duration.lower():
        #         course_item["teachingPeriod"] = 12
        #     else:
        #         course_item.add_flag("teachingPeriod", "New period found: " + duration)
        #
        #
        # yield course_item

    def course_parse(self, response):
        # if "online.jcu.edu.au" in response.request.url:
        #     self.counter += 1
        # print(self.counter)
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        # course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(cleanspace(name), self.uidPrefix)

        course_item.set_sf_dt(self.degrees, degree_delims=["-", ","])

        code = response.xpath("//td[preceding-sibling::td/p/strong/text()='Course code']/p/text()").get()
        if code:
            course_item["courseCode"] = cleanspace(code)

        summary = response.css("p.course-banner__text::text").get()
        if summary:
            course_item.set_summary(summary)

        locations = response.css("div.fast-facts-location li a::text").getall()
        if locations:
            locations = [cleanspace(x) for x in locations]
            mode_holder = []
            campuses = []
            for loc in locations:
                if loc == "Online":
                    mode_holder.append("Online")
                elif loc.lower() in list(self.campus_map.keys()):
                    campuses.append(self.campus_map[loc.lower()])
                    mode_holder.append("In person")
                else:
                    course_item.add_flag("campusNID", "New campus found: " + loc)
            course_item["campusNID"] = campuses
            course_item["modeOfStudy"] = mode_holder

        starts = response.css("div.fast-facts-commencing strong::text").getall()
        if starts:
            starts = ", ".join(starts).split(", ")
            starts = convert_months(starts)
            course_item["startMonths"] = starts

        duration_full = response.css("div.fast-facts-duration p:not(.part-time)::text").get()
        if duration_full:
            # if duration_full not in self.holder:
            #     self.holder.append(duration_full)
            value = re.findall("[\d\.]+", duration_full)
            if value:
                course_item["durationMinFull"] = value[0]
            else:
                course_item.add_flag("duration", "No duration value found: " + duration_full)
            if "year" in duration_full:
                course_item["teachingPeriod"] = 1
            else:
                course_item.add_flag("teachingPeriod", "No period found: " + duration_full)


        duration_part = response.css("div.fast-facts-duration p.part-time::text").get()
        if duration_part:
            value = re.findall("[\d\.]+", duration_part)
            if value:
                course_item["durationMinPart"] = value[0]
            # else:
            #     course_item.add_flag("duration", "No duration value found: " + duration_full)

        career = response.css("div#accordion_career p::text").getall()
        if career:
            course_item["careerPathways"] = "\n".join(career)

        overview = response.css("div#accordion_what-to-expect div.jcu-v1__accordion__content div")
        if overview:
            overview = overview[0].css("p::text").getall()
            if overview:
                course_item["overview"] = "\n".join(overview[:-1])

        fee = response.css("div.course-fast-facts__tile__body-top__lrg p::text").get()
        if fee:
            value = re.findall("[\d\.,]+", fee)
            if value:
                course_item["domesticFeeAnnual"] = value[0].replace(",", "").split(".")[0]

        international = response.xpath("//div[@class='course-fast-facts__header-links']/a[contains(text(),'International')]")
        if international:
            yield response.follow(response.request.url+"?international", callback=self.int_course_parse, meta={"item": course_item})
        else:
            if "campusNID" in course_item:
                course_item["campusNID"] = "|".join(course_item["campusNID"])
            if "modeOfStudy" in course_item:
                course_item["modeOfStudy"] = "|".join(list(set(course_item["modeOfStudy"])))
            if "startMonths" in course_item:
                course_item["startMonths"] = "|".join(list(set(course_item["startMonths"])))
            yield course_item

    def int_course_parse(self, response):
        course_item = response.meta["item"]

        course_item["internationalApps"] = 1
        # course_item["internationalApplyURL"] = response.request.url

        cricos = response.css("div.cricos-code p::text").get()
        if cricos:
            course_item["cricosCode"] = cricos.split(";")[0]

        fee = response.css("div.course-fast-facts__tile__body-top__lrg p::text").get()
        if fee:
            value = re.findall("[\d\.,]+", fee)
            if value:
                course_item["internationalFeeAnnual"] = value[0].replace(",", "").split(".")[0]

        locations = response.css("div.fast-facts-location li a::text").getall()
        try:
            campuses = course_item["campusNID"]
            course_item["campusNID"] = "|".join(course_item["campusNID"])
        except KeyError:
            campuses = []
        try:
            mode_holder = course_item["modeOfStudy"]
            course_item["modeOfStudy"] = "|".join(course_item["modeOfStudy"])
        except KeyError:
            mode_holder = []

        if locations:
            locations = [cleanspace(x) for x in locations]
            for loc in locations:
                if loc == "Online":
                    mode_holder.append("Online")
                elif loc.lower() in list(self.campus_map.keys()):
                    campuses.append(self.campus_map[loc.lower()])
                    mode_holder.append("In person")
                else:
                    course_item.add_flag("campusNID", "New campus found: " + loc)

            course_item["campusNID"] = "|".join(list(set(campuses)))
            course_item["modeOfStudy"] = "|".join(list(set(mode_holder)))

        starts = response.css("div.fast-facts-commencing strong::text").getall()
        if starts:
            starts = ", ".join(starts).split(", ")
            starts = convert_months(starts)

        if "startMonths" in course_item:
            course_item["startMonths"] = "|".join(list(set(course_item["startMonths"]+starts)))
        elif starts:
            course_item["startMonths"] = "|".join(list(set(starts)))

        yield course_item
