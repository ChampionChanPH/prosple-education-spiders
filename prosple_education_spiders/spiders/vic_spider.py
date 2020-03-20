import scrapy
import re
from ..items import Course
from datetime import date


class VicSpiderSpider(scrapy.Spider):
    name = 'vic_spider'
    allowed_domains = ['www.vu.edu.au', 'vu.edu.au']
    start_urls = ['https://www.vu.edu.au/search?f.Program+type%7Ccourses=Courses&f.Tabs%7CcourseTab=Courses+%26+units'
                  '&start_rank=1&query=%21showall&collection=vu-meta']
    courses = []
    counter = 1
    campuses = {"Werribee": "841", "Sunshine": "842", "St Albans": "847", "Industry": "845",
                "Footscray Nicholson": "849", "City Flinders": "844", "City Queen": "848",
                "Footscray Park": "840", "Sydney": "850", "Melbourne": "851", "City King St": "843"}
    months = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
              "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}

    def parse(self, response):
        self.courses.extend(response.xpath("//div[@class='search-result-list col-md-9']//li[@class='search-result "
                                           "search-result-course mb-3']/@data-fb-result").getall())

        while len(holder) > 0:
            next_page = "https://www.vu.edu.au/search?f.Program+type%7Ccourses=Courses&f.Tabs%7CcourseTab=Courses+%26" \
                        "+units&start_rank=" + str(self.counter * 10 + 1) + "&query=%21showall&collection=vu-meta"
            self.counter += 1
            yield response.follow(next_page, callback=self.parse)

        for course in self.courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["courseName"] = response.xpath("//h1[@class='page-header']/text()").get()
        course_item["courseCode"] = response.xpath("//div[contains(@class, 'field-name-field-unit-code')]//div["
                                                   "@class='field-item even ']/text()").get()
        course_item["cricosCode"] = response.xpath("//div[contains(@class, 'field-name-vucrs-cricos-code')]//div["
                                                   "@class='field-item even ']/text()").get()

        course_details = response.xpath("//section[@id='block-ds-extras-course-essentials']//div[@class='row']").get()
        full_duration = re.findall(r"[0-9]*?\.*?[0-9]+?(?=\s[years]+?\sfull.time)", course_details,
                                   re.DOTALL | re.MULTILINE)
        part_duration = re.findall(r"[0-9]*?\.*?[0-9]+?(?=\s[years]+?\spart.time)", course_details,
                                   re.DOTALL | re.MULTILINE)
        if len(full_duration) >= 1:
            course_item["durationMinFull"] = full_duration[0]
            course_item["teachingPeriod"] = 1
        if len(part_duration) >= 1:
            course_item["durationMinPart"] = part_duration[0]
            course_item["teachingPeriod"] = 1

        holder = []
        for campus in self.campuses:
            if re.search(campus, course_details, re.IGNORECASE):
                holder.append(self.campuses[campus])
        course_item["campusNID"] = "|".join(holder)

        holder = []
        for month in self.months:
            if re.search(month, course_details, re.IGNORECASE):
                holder.append(self.months[month])
        course_item["startMonths"] = "|".join(holder)

        holder = []
        if re.search("face", course_details, re.IGNORECASE):
            holder.append("In Person")
        if re.search("online", course_details, re.IGNORECASE):
            holder.append("Online")
        course_item["modeOfStudy"] = "|".join(holder)

        course_item["overviewSummary"] = response.xpath("//p[@class='paragraph--lead']/text()").get()
        course_item["overview"] = response.xpath(
            "//section[@id='description']//div[@class='field-item even ']").get()
        course_item["careerPathways"] = response.xpath(
            "//section[@id='careers']//div[@class='field-item even ']").get()
        course_item["whatLearn"] = response.xpath(
            "//div[@class='completion-rules']//div[@class='field-item even ']").get()
        course_item["howToApply"] = response.xpath("//div[@class='before-you-apply']").get()
        course_item["creditTransfer"] = response.xpath("//div[@id='accordion-pathways-credit-content']").get()

        course_item["domesticApplyURL"] = response.request.url
        course_item["internationalApplyURL"] = response.request.url

        international = response.xpath(
            "//div[@class='course-link']//div[contains(@class, 'non-residents')]//a/@href").get()

        if international is not None:
            yield response.follow(international, callback=self.international_parse, meta={'item': course_item})
            return

        yield course_item

    def international_parse(self, response):
        course_item = response.meta['item']
        course_details = response.xpath("//section[@id='block-ds-extras-course-essentials']//div[@class='row']").get()
        fee = re.findall("((?<=2020:\sA\$)|(?<=2020:\s\$))([0-9]{0,3}),?([0-9]{3})", course_details,
                         re.IGNORECASE | re.MULTILINE)
        if len(fee) >= 1:
            course_item["internationalFeeTotal"] = float("".join(fee[0])) * float(course_item["durationMinFull"]) * 2
            if float(course_item["durationMinFull"]) >= 1:
                course_item["internationalFeeAnnual"] = float("".join(fee[0])) * 2
            else:
                course_item["internationalFeeAnnual"] = course_item["internationalFeeTotal"]

        yield course_item
