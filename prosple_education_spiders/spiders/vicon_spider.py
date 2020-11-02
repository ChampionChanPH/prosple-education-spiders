# by: Johnel Bacani

from ..standard_libs import *


class ViconSpiderSpider(scrapy.Spider):
    name = 'vicon_spider'
    allowed_domains = ['online.vu.edu.au']
    start_urls = ['https://online.vu.edu.au/online-courses']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Victoria University (VU)"
    uidPrefix = "AU-VIC-ON-"

    degrees = {
        "master": "11"
    }

    def parse(self, response):
        courses = response.css("h3 a::attr(href)").getall()
        for course in courses:
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

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees)
        course_item["modeOfStudy"] = "Online"
        course_item["campusNID"] = "57342"

        overview = response.css(".overviewbody p::text").getall()
        if overview:
            course_item["overview"] = "\n".join(overview)
            course_item.set_summary(" ".join(overview))

        intakes = response.css("span.study p::text").get()
        if intakes:
            intakes = convert_months(intakes.replace(" ", "").split(","))
            course_item["startMonths"] = "|".join(intakes)

        fees = response.css("span.fees p::text").get()
        units = response.css("span.units p::text").get()
        if fees and units:
            fee = re.findall("\$([\d\.\,]+)", fees)[0]
            unit = re.findall("^(\d)+", units)[0]
            course_item["domesticFeeTotal"] = float(fee.replace(",", ""))*float(unit)
            course_item["internationalFeeTotal"] = float(fee.replace(",", ""))*float(unit)

        duration = response.css("span.duration p::text").get()
        if duration:
            value = re.findall("(\d+)\s\w+\spart-time", duration)[0]
            if value:
                course_item["durationMinPart"] = value
                if "month" in duration:
                    course_item["teachingPeriod"] = 12
                elif "year" in duration:
                    course_item["teachingPeriod"] = 1
                else:
                    course_item.add_flag("teachingPeriod", "Cannot find teaching period: "+duration)
        else:
            course_item.add_flag("duration", "Cannot find duration: "+duration)

        entry = response.xpath("//ul[preceding-sibling::h3/text()='Entry requirements']").get()
        if entry:
            course_item["entryRequirements"] = cleanspace(entry)

        else:
            entry = response.xpath("//p[preceding-sibling::h3/text()='Entry requirements']/text()").getall()
            if entry:
                course_item["entryRequirements"] = "\n".join(entry)

        titles = response.xpath("//ul[preceding-sibling::h4/text()='Typical job titles']").get()
        if titles:
            course_item["careerPathways"] = cleanspace(titles)
        yield course_item
