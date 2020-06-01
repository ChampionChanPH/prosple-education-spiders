# -*- coding: utf-8 -*-
# by Christian Anasco
# Update course level of "University Certificate in Tertiary Preparation for Postgraduate Studies" to Postgraduate
# Remove courses tagged non-award and not really courses like Scholarships, no overview summary
# Remove courses with name "last offered 2019"

from ..standard_libs import *
from ..scratch_file import strip_tags


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


class QutSpiderSpider(scrapy.Spider):
    name = 'qut_spider'
    allowed_domains = ['www.qut.edu.au', 'qut.edu.au']
    start_urls = ['https://www.qut.edu.au/study/undergraduate-study',
                  'https://www.qut.edu.au/study/postgraduate']
    institution = "QUT (Queensland University of Technology)"
    uidPrefix = "AU-QUT-"

    degrees = {
        "graduate certificate": "7",
        "executive graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "undergraduate certificate": "4",
        "university certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
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
        "Gardens Point": "685",
        "Canberra": "687",
        "Point Cook": "693",
        "Kelvin Grove": "684",
        "External": "686"
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

    def parse(self, response):
        study_area = response.xpath("//ul[@class='study-area-links']/li/a/@href").getall()

        for item in study_area:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[@id='course-category-listing-panel-tabs']/a[not(contains(@data-target, "
                             "'Overview-tab'))]/@href").getall()

        for item in sub:
            yield response.follow(item, callback=self.list_parse)

    def list_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'study-level')]//a/@href").getall()
        courses = [x for x in courses if not re.search("online.qut.edu.au", x)]

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/span/text()").get()
        if course_name is None:
            course_name = response.xpath("//h1/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview_summary = response.xpath("//div[contains(@class, 'hero__header__blurb')]/text()").get()
        if overview_summary:
            if overview_summary.strip() == "":
                overview_summary = response.xpath("//div[contains(@class, 'hero__header__blurb')]/p/text()").get()
        if overview_summary is not None:
            course_item.set_summary(overview_summary))

        overview = response.xpath("//*[contains(text(), 'Highlights')]/following-sibling::ul").get()
        if overview is not None:
            course_item["overview"] = strip_tags(overview, False)

        rank = response.xpath("//dd[@class='rank']/text()").get()
        if rank is not None:
            try:
                course_item["guaranteedEntryScore"] = float(rank.strip())
            except ValueError:
                course_item["guaranteedEntryScore"] = rank.strip()

        location = response.xpath("//dt[contains(text(), 'Campus')]/following-sibling::dd").get()
        campus_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        delivery = response.xpath("//dt[contains(text(), 'Delivery')]/following-sibling::dd/text()").get()
        study_holder = []
        if delivery is not None:
            if re.search("on.?campus", delivery, re.I):
                study_holder.append("In Person")
            if re.search("external", delivery, re.I):
                study_holder.append("Online")
                campus_holder.append(self.campuses["External"])
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)

        cricos = response.xpath("//dt[contains(text(), 'CRICOS')]/following-sibling::dd/text()").get()
        if cricos is not None:
            course_item["cricosCode"] = cricos.strip()
            course_item["internationalApps"] = 1
            course_item["internationalApplyURL"] = response.request.url

        course_code = response.xpath("//dt[contains(text(), 'Course code')]/following-sibling::dd/text()").get()
        if course_code is not None:
            course_item["courseCode"] = course_code.strip()

        duration = response.xpath("//div[@class='quick-box-inner']//dt[contains(text(), "
                                  "'Duration')]/following-sibling::dd[contains(@data-course-audience, "
                                  "'DOM')]").getall()
        duration_full = ""
        duration_part = ""
        if len(duration) > 0:
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.DOTALL | re.M)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
                                       duration, re.DOTALL | re.M)
        if len(duration_full) > 0:
            for item in self.teaching_periods:
                if re.search(item, duration_full[0][1], re.I):
                    course_item["teachingPeriod"] = self.teaching_periods[item]
        if "teachingPeriod" not in course_item and len(duration_part) > 0:
            for item in self.teaching_periods:
                if re.search(item, duration_part[0][1], re.I):
                    course_item["teachingPeriod"] = self.teaching_periods[item]
        if len(duration_full) > 0:
            course_item["durationMinFull"] = float(duration_full[0][0])
        if len(duration_part) > 0:
            if (course_item["teachingPeriod"] == 1 and duration_part[0][1] == "year") or \
                    (course_item["teachingPeriod"] == 12 and duration_part[0][1] == "month") or \
                    (course_item["teachingPeriod"] == 52 and duration_part[0][1] == "week"):
                course_item["durationMinPart"] = float(duration_part[0][0])
            if course_item["teachingPeriod"] == 12 and duration_part[0][1] == "year":
                course_item["durationMinPart"] = float(duration_part[0][0]) * 12
            if course_item["teachingPeriod"] == 1 and duration_part[0][1] == "month":
                course_item["durationMinPart"] = float(duration_part[0][0]) / 12

        start_months = response.xpath("//div[@class='quick-box-inner']//dt[contains(text(), "
                                      "'Course starts')]/following-sibling::dd[contains(@data-course-audience, "
                                      "'DOM')]").get()
        start_holder = []
        if start_months is not None:
            for month in self.months:
                if re.search(month, start_months, re.M):
                    start_holder.append(self.months[month])
        if len(start_holder) > 0:
            course_item["startMonths"] = "|".join(start_holder)

        career = response.xpath("//*[contains(text(), 'Careers and outcomes')]/following-sibling::*").getall()
        if len(career) > 0:
            course_item["careerPathways"] = strip_tags("".join(career), False)

        fee = response.xpath("//div[contains(@data-course-audience, 'DOM')]//div[contains(h3, "
                             "'2020 fees')]/following-sibling::div").getall()
        if len(fee) == 0:
            fee = response.xpath("//div[contains(@data-course-audience, 'DOM')]//div[contains(h3, "
                                 "'2021 fees')]/following-sibling::div").getall()
        dom_fee_holder = []
        csp_fee_holder = []
        if len(fee) > 0:
            fee = "".join(fee)
            dom_fee = re.findall("(?<!CSP\s)\$\d*,?\d{3}", fee, re.M)
            csp_fee = re.findall("(?<=CSP\s)\$\d*,?\d{3}", fee, re.M)
            if len(dom_fee) > 0:
                for item in dom_fee:
                    dom_fee_holder.append(float(re.sub("[\$,]", "", item)))
            if len(csp_fee) > 0:
                for item in csp_fee:
                    csp_fee_holder.append(float(re.sub("[\$,]", "", item)))
        if len(dom_fee_holder) > 0:
            course_item["domesticFeeAnnual"] = max(dom_fee_holder)
            get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
        if len(csp_fee_holder) > 0:
            course_item["domesticSubFeeAnnual"] = max(csp_fee_holder)
            get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        fee = response.xpath("//div[contains(@data-course-audience, 'INT')]//div[contains(h3, "
                             "'2020 fees')]/following-sibling::div").getall()
        if len(fee) == 0:
            fee = response.xpath("//div[contains(@data-course-audience, 'INT')]//div[contains(h3, "
                                 "'2021 fees')]/following-sibling::div").getall()
        int_fee_holder = []
        if len(fee) > 0:
            fee = "".join(fee)
            int_fee = re.findall("\$\d*,?\d{3}", fee, re.M)
            if len(int_fee) > 0:
                for item in int_fee:
                    int_fee_holder.append(float(re.sub("[\$,]", "", item)))
        if len(int_fee_holder) > 0:
            course_item["internationalFeeAnnual"] = max(int_fee_holder)
            get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        learn = response.xpath("//div[@id='what-to-expect-tab']/div/div/div").get()
        if learn is not None:
            course_item["whatLearn"] = strip_tags(learn, False)

        course_item.set_sf_dt(self.degrees)

        yield course_item
