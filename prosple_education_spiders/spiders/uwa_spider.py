# by: Johnel Bacani

from ..standard_libs import *


class UwaSpiderSpider(scrapy.Spider):
    name = 'uwa_spider'
    # allowed_domains = ['https://www.uwa.edu.au/study/courses-and-careers/find-a-course']
    start_urls = ['https://www.uwa.edu.au/study/courses-and-careers/find-a-course']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Western Australia (UWA)"
    uidPrefix = "AU-UWA-"
    lua_loadmore = """
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(2))
      local element = splash:select('.results-action-load-more')
      while element do
        assert(element:mouse_click())
        assert(splash:wait(.2))
        element = splash:select('.results-action-load-more')
      end
      return {
        html = splash:html(),
        png = splash:png(),
        har = splash:har(),
      }
    end
    """

    degree_delims = ["and"]

    def parse(self, response):
        yield SplashRequest(self.start_urls[0], callback=self.load_more, endpoint='execute',
                            args={'lua_source': self.lua_loadmore, 'url': self.start_urls[0]},
                            meta={'url': self.start_urls[0]})

    def load_more(self, response):
        courses = response.css(".result-item")
        print(len(courses))
        for item in courses:
            course = item.css("a.result-item::attr(href)").get()
            summary = item.css(".result-item-content p::text").get()
            level = item.xpath("//li[strong[contains(text(), 'Level:')]]/text()").get()
            # print(level)
            course_type = item.xpath("//li[strong[contains(text(), 'Type:')]]/span/text()").get()
            if course_type != "Undergraduate degree":
                print(course_type)
            if course_type == "Undergraduate Major":
                yield response.follow("https://www.uwa.edu.au"+course, callback=self.course_parse, meta={"summary": summary, "level": level, "course_type": course_type})

    def course_parse(self, response):
        def getfirst(raw):
            return raw[0]

        def monthsVal(raw):
            raw = " ".join(raw)
            months = convert_months(raw.split(" "))
            return "|".join(months)

        print(response.meta["course_type"])
        if response.meta["course_type"] == "Undergraduate Major":
            print("hey")
            return

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt()

        if response.meta["summary"]:
            course_item.set_summary(cleanspace(response.meta["summary"]))

        overview = response.css("#course-details .module-sub-title::text").get()
        if overview:
            course_item["overview"] = cleanspace(overview)

        #Extract course details
        divs = response.css(".card-details-dynamic div")
        trigger = False
        field_ref = {
            "cricos": {"field_name": "cricosCode", "value": getfirst},
            "course_code": {"field_name": "courseCode", "value": getfirst},
            "intake": {"field_name": "startMonths", "value": monthsVal},
        }
        for div in divs:
            text = div.css("div::text").get()
            if text:
                if "cricos" in text.lower():
                    trigger = True
                    field = "cricos"
                    course_item["internationalApps"] = 1
                    continue

                elif "course code" in text.lower():
                    trigger = True
                    field = "course_code"
                    continue

                elif "intake" in text.lower():
                    trigger = True
                    field = "intake"
                    continue

            if trigger:
                trigger = False
                value = div.css("li::text").getall()
                if value:
                    course_item[field_ref[field]["field_name"]] = field_ref[field]["value"](value)

        career = response.xpath("//div[preceding-sibling::h3/text()='Related careers']//ul").get()
        if career:
            course_item["careerPathways"] = career

        # labels = response.css(".card-details .card-details-label::text").getall()
        # values = response.css(".card-details .card-details-value li::text").getall()
        #
        # print(labels)
        # print(values)


        # if "flag" in course_item:
        #     yield course_item



