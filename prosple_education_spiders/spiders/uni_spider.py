# by: Johnel Bacani
# started: October 5, 2020

from ..standard_libs import *

class UniSpiderSpider(scrapy.Spider):
    name = 'uni_spider'
    allowed_domains = ['www.unitec.ac.nz']
    start_urls = ['https://www.unitec.ac.nz/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Unitec Institute of Technology"
    uidPrefix = "AU-UNI-"

    holder = []

    campuses = {
        'Waitākere': "0000",
        'North Shore': "0000",
        'Mt Albert': "0000"
    }

    def parse(self, response):
        course_cards = response.css(".progrow:not(#progrow):not(.overview)")
        for card in course_cards:
            course = re.findall("'(.*?)'", card.css("div::attr(onclick)").get())[0]
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

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        campus = response.css("dl.programme-campus dd::text").getall()
        if campus:
            campus = " ".join(campus).split(",")
            campus = [cleanspace(x) for x in campus if cleanspace(x) != ""]
            holder = []
            for i in campus:
                if i in list(self.campuses.keys()):
                    holder.append(self.campuses[i])
                else:
                    course_item.add_flag("campusNID", "New campus found: "+i)
            course_item["campusNID"] = "'"+"|".join(holder)

        dates = response.css("dl.programme-dates dd::text").get()
        if dates:
            months = convert_months(dates.replace(",", "").split(" "))
            course_item["startMonths"] = "'"+"|".join(months)

        duration = response.css("dl.programme-duration dd::text").get()
        # if duration:
        #     print(duration)

        summary = response.css(".page-detail__column p::text").get()
        if summary:
            course_item["overviewSummary"] = summary

        yield course_item
