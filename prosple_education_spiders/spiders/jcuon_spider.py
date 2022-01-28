# by: Johnel Bacani

from ..standard_libs import *

class JcuonSpiderSpider(scrapy.Spider):
    name = 'jcuon_spider'
    allowed_domains = ['online.jcu.edu.au']
    start_urls = ['https://online.jcu.edu.au/online-courses']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "James Cook University (JCU)"
    uidPrefix = "AU-JCU-ON-"

    degrees = {
        "master": "11",
        "online graduate diploma": "8",
        "online graduate certificate": "7",
    }

    def parse(self, response):

        courses = response.css(".courseblock .content ul li a::attr(href)").getall()
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
        # course_item["campusNID"] = "57650"

        name = response.css("figure h1::text").get()
        if name:
            name = cleanspace(name)
            course_item.set_course_name(name, self.uidPrefix)
        course_item.set_sf_dt(self.degrees)
        course_item["modeOfStudy"] = "Online"

        summary = response.css(".stuckright p::text").getall()
        if summary:
            course_item.set_summary(" ".join(summary))

        overview = response.css(".stuckright div").get()
        if overview:
            overview = re.sub("<\/?div.*?>", "", overview)
            overview = re.sub("<\/?a.*?>", "", overview)
            overview = re.sub("<p.*?Download Course Guide</p>", "", overview)
            overview = re.sub("<p id=\"duration.*?</p>", "", overview)
            # print(cleanspace(overview))
            course_item["overview"] = cleanspace(overview)


        learn = response.xpath("//div[preceding-sibling::header/h2[contains(text(),'you will study')]]/p/text()").getall()
        if learn:
            course_item["whatLearn"] = "<br><br>".join([cleanspace(x) for x in learn])

        start = response.css(".views-field-field-course-study-periods div::text").get()
        if start:
            course_item["startMonths"] = "|".join(convert_months([cleanspace(x) for x in start.split(",")]))

        fee = response.css(".views-field-field-course-fees .field-content::text").get()
        if fee:
            per_subject = re.findall("\$([\d\.,]+)\sper subject", fee)
            if per_subject:
                subjects = response.css(".views-field-field-course-subjects .field-content::text").get()
                if subjects:
                    course_item["domesticFeeTotal"] = float(per_subject[0].replace(",", "")) * float(subjects)
                    course_item["internationalFeeTotal"] = float(per_subject[0].replace(",", "")) * float(subjects)

        duration = response.css(".views-field-field-course-duration div::text").get()
        if duration:
            value = re.findall("[\d\.]+", duration)
            if value:
                if "part-time" in duration:
                    course_item["durationMinPart"] = value[0]
                else:
                    course_item["durationMinFull"] = value[0]
            if "month" in duration.lower():
                course_item["teachingPeriod"] = 12
            else:
                course_item.add_flag("teachingPeriod", "New period found: " + duration)

        rpl = response.xpath("//section/div[preceding-sibling::header/h2[contains(text(),'Recognition of Prior Learning')]]/p/text()").getall()
        if rpl:
            course_item["creditTransfer"] = "\n".join([cleanspace(x) for x in rpl])

        entry = response.xpath("//section/div/ul[preceding-sibling::h2[contains(text(),'Entry')]]").get()
        if entry:
            entry = re.sub('(<\w+)(\s[^>]+)', r"\1", entry)
            course_item["entryRequirements"] = cleanspace(entry)

        yield course_item

