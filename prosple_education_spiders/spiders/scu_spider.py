import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class ScuSpiderSpider(scrapy.Spider):
    name = 'scu_spider'
    allowed_domains = ['www.scu.edu.au', 'scu.edu.au']
    start_urls = ['https://www.scu.edu.au/study-at-scu/course-search/?mkeyword=&year=2020&keyword=']
    courses = []
    campuses = {
        "Melbourne": "701",
        "Lismore": "695",
        "Gold Coast": "696",
        "Perth": "700",
        "Sydney": "699",
        "Tweed Heads": "698",
        "Coffs Harbour": "697",
        "National Marine Science Centre": "694"
    }
    key_dates = {
        "1": "03",
        "2": "07",
        "3": "11"
    }
    degrees = {
        "Graduate Certificate": "Graduate Certificate",
        "Graduate Diploma": "Graduate Diploma",
        "Honours": "Bachelor (Honours)",
        "Research": "Masters (Research)",
        "Master": "Masters (Coursework)",
        "Doctor": "Doctorate (PhD)",
        "Bachelor": "Bachelor",
        "Associate Degree": "Associate Degree",
        "Certificate": "Certificate",
        "Diploma": "Diploma"
    }
    group = [["Postgraduate", 4, "PostgradAustralia"], ["Undergraduate", 3, "The Uni Guide"]]

    def parse(self, response):
        self.courses.extend(response.xpath("//div[@class='courses-table-wrap']//td/a/@href").getall())

        next_page = response.xpath("//ul[@class='pagination']//a[@class='pbc-pag-next']/@href").get()

        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

        for course in self.courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "Southern Cross University (SCU)"
        uidPrefix = "AU-SCU-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='pageTitleFixSource']/text()").get()
        course_item["courseName"] = course_name.strip()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        for degree in self.degrees:
            if re.search(degree, course_item["courseName"], re.I):
                course_item["degreeType"] = self.degrees[degree]
                break
        if "degreeType" not in course_item:
            course_item["degreeType"] = "Non-Award"
        if course_item["degreeType"] in ["Graduate Certificate", "Graduate Diploma", "Bachelor (Honours)",
                                         "Masters (Research)", "Masters (Coursework)", "Doctorate (PhD)"]:
            course_item["courseLevel"] = self.group[0][0]
            course_item["group"] = self.group[0][1]
            course_item["canonicalGroup"] = self.group[0][2]
        elif course_item["degreeType"] in ["Bachelor", "Certificate", "Diploma", "Associate Degree"]:
            course_item["courseLevel"] = self.group[1][0]
            course_item["group"] = self.group[1][1]
            course_item["canonicalGroup"] = self.group[1][2]
        else:
            course_item["courseLevel"] = ""
            course_item["group"] = self.group[1][1]
            course_item["canonicalGroup"] = self.group[1][2]
        separate_holder = re.split(",\s(?=Bachelor|Graduate|Diploma|Master|Doctor|Associate|Certificate)", course_item["courseName"])
        if len(separate_holder) == 1:
            separate_holder = re.split("/", course_item["courseName"])
        if len(separate_holder) > 1:
            course_item["doubleDegree"] = 1
        holder = []
        for item in separate_holder:
            if re.search("\s(in|of)\s", item):
                holder.append(re.findall("(?<=[in|of]\s)(.+)", item, re.DOTALL)[0])
            else:
                holder.append(item)
        course_item["specificStudyField"] = "/".join(holder)
        lower_holder = []
        for item in holder:
            lower_holder.append(item.lower())
        course_item["rawStudyfield"] = lower_holder[:]

        course_code = response.xpath("//div[@class='standard-banner__wrapper']//p[contains(text(), 'Course "
                                     "Code')]/text()").get()
        course_code = re.findall("(?<=Course Code: )\w+", course_code, re.I)
        if len(course_code) > 0:
            course_item["courseCode"] = course_code[0]
        summary = response.xpath("//div[@class='col-migrate-lg-6']/div[contains(@class, 'summary')]/div/p").getall()
        summary = "".join(summary)
        course_item["overview"] = strip_tags(summary, False)

        check_dom = response.xpath("//ul[@id='sub_menu']/li[contains(@class, 'yes-t4show')]/a[contains(text(), "
                                   "'Domestic')]").getall()
        check_int = response.xpath("//ul[@id='sub_menu']/li[contains(@class, 'yes-t4show')]/a[contains(text(), "
                                   "'International')]").getall()

        if len(check_dom) > 0:
            get_details = response.xpath("//div[@id='domestic']//tbody").get()
            session = response.xpath("//div[@id='domestic']//tbody/tr/td[2]//tbody/tr/td[2]/text()").getall()
        elif len(check_int) > 0:
            get_details = response.xpath("//div[@id='international']//tbody").get()
            session = response.xpath("//div[@id='international']//tbody/tr/td[2]//tbody/tr/td[2]/text()").getall()
        duration_full = re.findall("(\d?\.?\d+?)(?=.?(years|year|weeks|week).?full.?time)", get_details,
                                   re.MULTILINE | re.IGNORECASE)
        duration_part = re.findall("(\d?\.?\d+?)(?=.?(years|year|weeks|week).?part.?time)", get_details,
                                   re.MULTILINE | re.IGNORECASE)
        session = ", ".join(session)
        start_months = []
        for item in self.key_dates:
            if re.search(item, session):
                start_months.append(self.key_dates[item])
        course_item["startMonths"] = "|".join(start_months)

        if len(duration_full) > 0:
            course_item["durationMinFull"] = duration_full[0][0]
            if re.search("years?", duration_full[0][1]):
                course_item["teachingPeriod"] = 1
            if re.search("weeks?", duration_full[0][1]):
                course_item["teachingPeriod"] = 52
        elif len(duration_part) > 0:
            if re.search("years?", duration_part[0][1]):
                course_item["teachingPeriod"] = 1
            if re.search("weeks?", duration_part[0][1]):
                course_item["teachingPeriod"] = 52
        if len(duration_part) > 0:
            course_item["durationMinPart"] = duration_part[0][0]

        get_int_details = ""
        get_dom_details = ""
        if len(check_int) > 0:
            course_item["internationalApps"] = 1
            get_int_details = response.xpath("//div[@id='international']//tbody/tr/td[contains(text(), "
                                             "'Availability')]/following-sibling::td").get()
        if len(check_dom) > 0:
            get_dom_details = response.xpath("//div[@id='domestic']//tbody/tr/td[contains(text(), "
                                             "'Availability')]/following-sibling::td").get()
        campus_holder = []
        study_holder = []
        if len(get_dom_details) > 0:
            for campus in self.campuses:
                if re.search(campus, get_dom_details, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
            if re.search("Online", get_dom_details, re.I | re.M):
                study_holder.append("Online")
        elif len(get_int_details) > 0:
            for campus in self.campuses:
                if re.search(campus, get_dom_details, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if re.search("Online", get_dom_details, re.I | re.M):
                study_holder.append("Online")
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)
        if "campusNID" in course_item:
            study_holder.append("In Person")
        course_item["modeOfStudy"] = "|".join(study_holder)

        if len(get_dom_details) > 0:
            dom_fee = re.findall("\$(\d+),?(\d{3})", get_dom_details, re.M)
            fee_holder = []
            for item in dom_fee:
                fee_holder.append(float("".join(item)))
            if len(fee_holder) > 0:
                course_item["domesticFeeAnnual"] = max(fee_holder)
        if len(get_int_details) > 0:
            int_fee = re.findall("\$(\d+),?(\d{3})", get_int_details, re.M)
            fee_holder = []
            for item in int_fee:
                fee_holder.append(float("".join(item)))
            if len(fee_holder) > 0:
                course_item["internationalFeeAnnual"] = max(fee_holder)

        if "durationMinFull" in course_item and "teachingPeriod" in course_item and "domesticFeeAnnual" in course_item:
            if course_item["teachingPeriod"] == 1:
                if float(course_item["durationMinFull"]) < 1:
                    course_item["domesticFeeTotal"] = course_item["domesticFeeAnnual"]
                else:
                    course_item["domesticFeeTotal"] = float(course_item["durationMinFull"]) * course_item["domesticFeeAnnual"]

        if "durationMinFull" in course_item and "teachingPeriod" in course_item and "internationalFeeAnnual" in course_item:
            if course_item["teachingPeriod"] == 1:
                if float(course_item["durationMinFull"]) < 1:
                    course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"]
                else:
                    course_item["internationalFeeTotal"] = float(course_item["durationMinFull"]) * course_item["internationalFeeAnnual"]

        if len(get_int_details) > 0:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", get_int_details, re.M)
            cricos = set(cricos)
            cricos = ", ".join(cricos)
            course_item["cricosCode"] = cricos

        for header, content in zip(
                response.xpath("//div[@role='tablist' and @class='accordion']//div/h3/text()").getall(),
                response.xpath("//div[@role='tablist' and @class='accordion']/div["
                               "@class='accordion-group']/div/div").getall()):
            if re.search(r"career opportunities", header, re.I | re.M):
                career = strip_tags(content, False)
                course_item["careerPathways"] = career

        yield course_item
