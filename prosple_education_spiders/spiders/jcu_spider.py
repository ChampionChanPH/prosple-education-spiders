# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by: Christian Anasco on 4th May, 2021

from ..standard_libs import *
from ..scratch_file import strip_tags


def research_coursework(course_item):
    if re.search("research", course_item["courseName"], re.I):
        return "12"
    else:
        return "11"


def bachelor_honours(course_item):
    if re.search("honours", course_item["courseName"], re.I) or re.search("hons", course_item["courseName"], re.I):
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


class JcuSpiderSpider(scrapy.Spider):
    name = 'jcu_spider'
    start_urls = ['https://www.jcu.edu.au/courses/study']
    institution = "James Cook University (JCU)"
    uidPrefix = "AU-JCU-"

    campuses = {
        "mount isa": "53598",
        "mackay": "53604",
        "townsville": "620",
        "singapore": "621",
        "brisbane": "619",
        "cairns": "618"
    }

    degrees = {
        "online graduate certificate": "7",
        "graduate certificate": "7",
        "postgraduate certificate": "7",
        "online graduate diploma": "8",
        "graduate diploma": "8",
        "postgraduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "senior executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "doctoral program": "6",
        "certificate": "4",
        "specialist certificate": "4",
        "professional certificate": "14",
        "undergraduate certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "juris doctor": "10",
        "non-award": "13",
        "no match": "15"
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

    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//ul[@class='jcu-v1__ct__link-list__container']//a")
        yield from response.follow_all(categories, callback=self.category_parse)

    def category_parse(self, response):
        courses = response.xpath("//a[@class='jcu-v1__search__heading']/@href").getall()
        if courses:
            courses = response.xpath("//a[@class='jcu-v1__search__heading']")
            yield from response.follow_all(courses, callback=self.course_parse)
        else:
            categories = response.xpath("//a[@class='jcu-v1__ct__usp__tile-link'][not(div/div/p/text())]")
            yield from response.follow_all(categories, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//a[@class='jcu-v1__search__heading']")
        yield from response.follow_all(courses, callback=self.course_parse)

    # def online_course_parse(self, response):
    # course_item = Course()
    # course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
    # course_item["sourceURL"] = response.request.url
    # course_item["published"] = 1
    # course_item["institution"] = self.institution
    #
    # name = response.css("figure h1::text").get()
    # if name:
    #     course_item.set_course_name(name, self.uidPrefix)
    # course_item.set_sf_dt(self.degrees, degree_delims=["-", ","])
    # course_item["modeOfStudy"] = "Online"
    #
    # overview = response.css(".stuckright p::text").getall()
    # if overview:
    #     course_item["overview"] = "\n".join(overview[:-1])
    #     course_item.set_summary(" ".join(overview[:-1]))
    #
    # start = response.css(".views-field-field-course-study-periods div::text").get()
    # if start:
    #     course_item["startMonths"] = "|".join(convert_months([cleanspace(x) for x in start.split(",")]))
    #
    # duration = response.css(".views-field-field-course-duration div::text").get()
    # if duration:
    #     value = re.findall("[\d\.]+", duration)
    #     if value:
    #         if "part-time" in duration:
    #             course_item["durationMinPart"] = value[0]
    #         else:
    #             course_item["durationMinFull"] = value[0]
    #     if "month" in duration.lower():
    #         course_item["teachingPeriod"] = 12
    #     else:
    #         course_item.add_flag("teachingPeriod", "New period found: " + duration)
    #
    #
    # yield course_item

    def course_parse(self, response):
        # if "online.jcu.edu.au" in response.request.url:
        #     self.counter += 1
        # print(self.counter)
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[@class='course-banner__text']").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        course_code = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), 'Course "
                                     "Code')]/following-sibling::*//p/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        location = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), "
                                  "'Location')]/following-sibling::*").get()
        campus_holder = []
        study_holder = []
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
            if re.search('online', location, re.I | re.M):
                study_holder.append('Online')
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)
            study_holder.append('In Person')
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        intake = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), "
                                "'Commencing')]/following-sibling::*").get()
        if intake:
            start_holder = []
            for month in self.months:
                if re.search(month, intake, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        duration = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), "
                                  "'Duration')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s+?part)",
                duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    # course_item["durationMinFull"] = float(duration_full[0][0])
                    # self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        entry = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), 'Entry "
                               "Requirements')]/following-sibling::*/*["
                               "@class='course-fast-facts__tile__body-top']/*").getall()
        if entry:
            entry = ''.join(entry)
            if re.search('ATAR', entry):
                atar = re.findall('(?<=ATAR )\d{1,3}\.?\d*', entry)
                if atar:
                    atar = [float(x) for x in atar]
                    course_item['guaranteedEntryScore'] = max(atar)
            course_item['entryRequirements'] = strip_tags(entry, remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//button[contains(text(), 'Career Opportunities')]/following-sibling::*//*[contains("
                                "@id, 'content_container')]/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath("//button[contains(text(), 'How to apply')]/following-sibling::*//*[contains(@id, "
                               "'content_container')]/*").getall()
        if apply:
            course_item["howToApply"] = strip_tags(''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        fee = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), "
                             "'Fees')]/following-sibling::*").get()
        if fee:
            dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?(?=<sup>\^)", fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

            csp_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?(?=<sup>\+)", fee, re.M)
            csp_fee = [float(''.join(x)) for x in csp_fee]
            if csp_fee:
                course_item["domesticSubFeeAnnual"] = max(csp_fee)
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/', ','], type_delims=['of', 'in', 'by'])

        international = response.xpath("//*[@class='course-fast-facts__header-links']//a[contains(text(), "
                                       "'International')]/@href").get()
        if international:
            yield response.follow(international, callback=self.international_parse, meta={"item": course_item})
        else:
            yield course_item

    def international_parse(self, response):
        course_item = response.meta["item"]

        course_item["internationalApps"] = 1
        course_item["internationalApplyURL"] = response.request.url

        cricos = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), 'CRICOS "
                                "Code')]/following-sibling::*//p/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)

        int_fee = response.xpath("//*[@class='course-fast-facts__tile__header'][contains(*/text(), "
                                 "'Fees')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?(?=<sup>\+)", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        yield course_item
