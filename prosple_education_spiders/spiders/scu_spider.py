# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


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
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class ScuSpiderSpider(scrapy.Spider):
    name = 'scu_spider'
    start_urls = ['https://course-search.scu.edu.au/']
    institution = "Southern Cross University (SCU)"
    uidPrefix = "AU-SCU-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "vcal in victorian certificate": "9",
        "vcal in": "9",
        "non-award": "13",
        "no match": "15"
    }

    months = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"
    }

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

    teaching_periods = {
        "year": 1,
        "semester": 2,
        "trimester": 3,
        "quarter": 4,
        "month": 12,
        "week": 52,
        "day": 365
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//div[@class='row results']//a[contains(@class, 'text-primary')]/@href").getall()

        for item in courses:
            yield response.follow(item.strip(), callback=self.course_parse)

        next_page = response.xpath("//a[@class='page-link'][contains(*/@class, 'angle-right')]/@href").getall()

        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        # course_item["internationalApplyURL"] = response.request.url
        # course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='pageTitleFixSource']/text()").get()
        course_item["courseName"] = course_name.strip()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        degree_holder =[]
        for degree in self.degrees:
            if re.search(degree, course_item["courseName"], re.IGNORECASE):
                degree_holder.append(self.degrees[degree])
        if len(degree_holder) > 0:
            course_item["degreeType"] = max(degree_holder)
        if "degreeType" not in course_item:
            course_item["degreeType"] = "Non-Award"
            course_item.add_flag("degreeType", "assigned non-award")
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
        separate_holder = re.split("\s?[,/]\s?(?=Bachelor|Graduate|Diploma|Masters|Doctor|Associate|Certificate)",
                                   course_item["courseName"], re.I | re.M)
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

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        yield course_item
