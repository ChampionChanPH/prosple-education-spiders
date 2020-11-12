# by: Johnel Bacani

from ..standard_libs import *


class AcpSpiderSpider(scrapy.Spider):
    name = 'acp_spider'
    allowed_domains = ['acpe.edu.au']
    start_urls = ['https://acpe.edu.au/future-students/study/courses/']

    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "James Cook University (JCU)"
    uidPrefix = "AU-ACP-"

    degrees = {
        "undergraduate certificate": "4",
    }

    def parse(self, response):
        course_cards = response.css(".wpb_wrapper div[data-test]")
        course_info = response.xpath("//div[@data-test]/following-sibling::div[1]").getall()

        if len(course_cards) == len(course_info):
            for i in range(len(course_cards)):
                info = course_cards[i].css(".col-md-9::text").get()
                if info:
                    summary = info.split(".")[0]+"."
                    cricos = re.findall("CRICOS\s(\w+)", info)

                course = course_cards[i].css("a::attr(href)").get()
                quick_info = course_info[i]

                if course not in self.blacklist_urls and course not in self.scraped_urls:
                    if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                        self.scraped_urls.append(course)
                        yield response.follow(course, callback=self.course_parse, meta={"summary": summary, "cricos": cricos, "quick_info": quick_info})

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

        if response.meta["summary"]:
            course_item.set_summary(response.meta["summary"])

        if response.meta["cricos"]:
            course_item["cricosCode"] = response.meta["cricos"][0]
            course_item["internationalApps"] = 1


        if response.meta["quick_info"]:
            quick_info = response.meta["quick_info"]
            duration = re.findall("DURATION</h4>(.*?)<", quick_info)
            if duration:
                course_item["durationRaw"] = duration
                years = re.findall("([\d\.]+)\s?Y Full Time", duration[0])
                months = re.findall("([\d\.]+) Months Full Time", duration[0])
                if years:
                    course_item["durationMinFull"] = years[0]
                    course_item["teachingPeriod"] = 1

                elif months:
                    course_item["durationMinFull"] = months[0]
                    course_item["teachingPeriod"] = 12

                else:
                    course_item.add_flag("duration", "New duration pattern found: "+duration)

            if "mixed mode" in quick_info.lower():
                course_item["modeOfStudy"] = "In Person|Online"
            elif "online" in quick_info.lower():
                course_item["modeOfStudy"] = "Online"

            intake = re.findall("NEXT INTAKE</h4>(.*?)<", quick_info)
            if intake:
                months = convert_months(intake[0].split(" "))
                course_item["startMonths"] = "|".join(months)
        overview = response.xpath("//*[preceding-sibling::h3/text()= 'About the course']").getall()
        if overview:
            overview = "\n".join(overview)
            overview = re.sub("<\/?div.*?>", "", overview)
            overview = re.sub("<\/?a.*?>", "", overview)
            overview = re.sub('(<\w+)(\s[^>]+)', r"\1", overview)

            course_item["overview"] = cleanspace(overview)
        # if "flag" in course_item:
        yield course_item


