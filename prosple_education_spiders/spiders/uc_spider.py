# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class UcSpiderSpider(scrapy.Spider):
    name = 'uc_spider'
    # allowed_domains = ['https://www.canterbury.ac.nz/study/qualifications-and-courses']
    start_urls = ['https://www.canterbury.ac.nz/study/qualifications-and-courses/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "https://www.canterbury.ac.nz/study/qualifications-and-courses/bachelors-degrees/double-degrees/",
        "https://www.canterbury.ac.nz/study/study-abroad-and-exchange/outgoing-exchange-current-uc-students/insurance-for-outgoing-students/"
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "University of Canterbury"
    uidPrefix = "NZ-UC-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "professional master": "11",
        # "diploma for graduates": "8"
    }

    holder = []

    def parse(self, response):
        courses = ["https://www.canterbury.ac.nz/study/qualifications-and-courses/certificate-of-proficiency/"]
        for i in range(7):
            selector = "ul#subsubmenu-"+str(i+2)+" a::attr(href)"
            courses = courses + response.css(selector).getall()

        for course in [x for x in courses if x[0] != "#" and "/subjects/" not in x]:
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
        course_item["campusNID"] = "48599"

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(cleanspace(name), self.uidPrefix)

        # course_code = response.css("h3.acronym::text").get()
        # if course_code:
        #     course_item["courseCode"] = course_code

        course_item.set_sf_dt(self.degrees)

        # Overide canonical group
        course_item["group"] = 2
        course_item["canonicalGroup"] = "GradNewZealand"

        summary = response.css(".Lead_paragraph::text").get()
        if summary:
            course_item.set_summary(cleanspace(summary))

        overview = response.css("#overview").get()
        if overview:
            overview = re.sub("<.*?>", "", overview)
            course_item["overview"] = overview
        #
        # entry = response.xpath("//div[preceding-sibling::div/h4/a/text()='Entry requirements']/div[1]").get()
        # if entry:
        #     entry = re.sub("</?div.*?>", "", entry)
        #     course_item["entryRequirements"] = entry
        #
        career = response.xpath("//div[preceding-sibling::div/h4/a/text()='Career Opportunities']").get()
        if career:
            career = re.sub("</?div.*?>", "", career)
            course_item["careerPathways"]

        duration = response.xpath("//p[preceding-sibling::h3/text()='Duration']/text()").get()
        if duration:
            if "year" in duration.lower():
                course_item["teachingPeriod"] = 1
            elif "semester" in duration.lower():
                course_item["teachingPeriod"] = 2
            elif "month" in duration.lower():
                course_item["teachingPeriod"] = 12
            elif "week" in duration.lower():
                course_item["teachingPeriod"] = 52
            else:
                course_item.add_flag("teachingPeriod", "No teaching period found: "+duration)

            if "full" in duration.lower():
                field = "Full"
            elif "part" in duration.lower():
                field = "Part"
            else:
                field = "Full"

            values = re.findall("[\d\.]+", duration)
            if len(values) == 1:
                if "up to" in duration.lower():
                    course_item["durationMax" + field] = values[0]
                else:
                    course_item["durationMin" + field] = values[0]
            elif len(values) > 1:
                course_item["durationMin" + field] = min([float(x) for x in values])
                course_item["durationMax" + field] = max([float(x) for x in values])

            elif "Two" in duration:
                course_item["durationMin" + field] = 2

            else:
                course_item.add_flag("duration", "No duration value found: " + duration)

        intake = response.xpath("//p[preceding-sibling::h3/text()='Entry times']/text()").get()
        if intake:
            intake = re.findall("\w+", intake)
            intake = convert_months(intake)
            course_item["startMonths"] = "|".join(intake)

        domestic_fee = response.xpath("//div[preceding-sibling::div/h4/a/text()='Tuition Fees']/div/div[@id='domfee']//tr[2]/td[4]/text()").get()
        if domestic_fee:
            domestic_fee = re.findall("\$([\d,\.]+)", domestic_fee)
            if domestic_fee:  # If any matches were found
                domestic_fee = [int(float(x.replace(",", ""))) for x in domestic_fee]
                course_item["domesticFeeAnnual"] = max(domestic_fee)

        international_fee = response.xpath("//div[preceding-sibling::div/h4/a/text()='Tuition Fees']/div/div[@id='intefee']//tr[2]/td[4]/text()").get()
        if international_fee:
            international_fee = re.findall("\$([\d,\.]+)", international_fee)
            if international_fee:  # If any matches were found
                international_fee = [int(float(x.replace(",", ""))) for x in international_fee]
                course_item["internationalFeeAnnual"] = max(international_fee)
                course_item["internationalApps"] = 1

        # if "flag" in course_item:
        # yield course_item

