# -*- coding: utf-8 -*-
# by Christian Anasco

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
    banned_urls = ['https://www.qut.edu.au/law/study/professional-development',
                   'https://www.qut.edu.au/law/research/study',
                   'https://www.qut.edu.au/law/study/scholarships-and-support',
                   'https://www.qut.edu.au/law/study/real-world-learning',
                   'https://www.qut.edu.au/study/professional-and-executive-education/single-unit-study/law-and-justice',
                   'https://www.qut.edu.au/law/research/our-experts',
                   'https://www.qut.edu.au/law/study/international-experience',
                   'https://www.qut.edu.au/law/study/work-experience',
                   'https://www.qut.edu.au/study/fees-and-scholarships/scholarships/excellence-scholarship-academic'
                   ]
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
        "undergraduate certificate": "4",
        "university certificate": "4",
        "certificate": "4",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//ul[contains(@class, 'study-area-links')]/li/a")
        yield from response.follow_all(categories, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//ul[contains(@class, 'study-area-links')]/li/a")

        for item in sub:
            yield response.follow(item, callback=self.link_parse)

    def link_parse(self, response):
        courses = response.xpath("//a[contains(@class, 'course-page-link')]/@href").getall()
        courses = [x for x in courses if not re.search("online.qut.edu.au", x)]

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url + \
                                          r"?utm_source=referral_partner&utm_medium=prosple&utm_campaign" \
                                          r"=prosple_course_listing&utm_content=&utm_term=&spad=prosple "

        course_name = response.xpath("//h1/span/text()").get()
        if not course_name:
            course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath("//div[contains(@class, 'hero__header__blurb')]/text()").get()
        if summary:
            if summary.strip() == '':
                summary = response.xpath("//div[contains(@class, 'hero__header__blurb')]/p/text()").get()
            course_item.set_summary(summary)
        if 'overviewSummary' not in course_item:
            summary = response.xpath("//*[contains(text(), 'Highlights')]/following-sibling::ul/*").getall()
            if not summary:
                summary = response.xpath("//*[contains(text(), 'Highlights')]/following-sibling::*").get()
            if summary:
                summary = [strip_tags(x) for x in summary]
                course_item.set_summary(' '.join(summary))

        overview = response.xpath("//*[contains(text(), 'Highlights')]/following-sibling::ul").get()
        if not overview:
            overview = response.xpath("//*[contains(text(), 'Highlights')]/following-sibling::*").get()
        if overview:
            course_item["overview"] = strip_tags(overview, remove_all_tags=False, remove_hyperlinks=True)

        rank = response.xpath("//dd[@class='rank']/text()").get()
        if rank:
            try:
                course_item["guaranteedEntryScore"] = float(rank.strip())
            except ValueError:
                pass

        location = response.xpath("//div[contains(@class, 'quick-boxes')]//div[contains(@class, "
                                  "'quick-box-info-lists')]//dt[contains(text(), "
                                  "'Delivery')]/following-sibling::dd").get()
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
            if re.search('online', location, re.I):
                study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        cricos = response.xpath("//dt[contains(text(), 'CRICOS')]/following-sibling::dd").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url + \
                                                       r"?utm_source=referral_partner&utm_medium=prosple&utm_campaign" \
                                                       r"=prosple_course_listing&utm_content=&utm_term=&spad=prosple "
        course_code = response.xpath("//dt[contains(text(), 'Course code')]/following-sibling::dd/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        duration = response.xpath("//div[contains(@class, 'quick-boxes')]//div[contains(@class, "
                                  "'quick-box-info-lists')]//dt[contains(text(), "
                                  "'Duration')]/following-sibling::dd").get()
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
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        intake = response.xpath("//div[contains(@class, 'quick-boxes')]//div[contains(@class, "
                                "'quick-box-info-lists')]//dt[contains(text(), 'Course "
                                "starts')]/following-sibling::dd").get()
        holder = []
        if intake:
            for month in self.months:
                if re.search(month, intake, re.M):
                    holder.append(self.months[month])
        if holder:
            course_item["startMonths"] = "|".join(holder)

        career = response.xpath("//*[@id='career-outcomes-tab']//div[contains(@class, 'panel-content')]/*/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        fee = response.xpath("//div[contains(@data-course-audience, 'DOM')]//div[contains(h3, '202') or contains(h3, "
                             "'fees')]/following-sibling::div").getall()
        dom_fee_holder = []
        csp_fee_holder = []
        if fee:
            fee = ''.join(fee)
            dom_fee = re.findall("(?<!CSP\s)\$\d*,?\d{3}", fee, re.M)
            csp_fee = re.findall("(?<=CSP\s)\$\d*,?\d{3}", fee, re.M)
            if dom_fee:
                for item in dom_fee:
                    dom_fee_holder.append(float(re.sub("[\$,]", "", item)))
            if csp_fee:
                for item in csp_fee:
                    csp_fee_holder.append(float(re.sub("[\$,]", "", item)))
        if dom_fee_holder:
            course_item["domesticFeeAnnual"] = max(dom_fee_holder)
            get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
        if csp_fee_holder:
            course_item["domesticSubFeeAnnual"] = max(csp_fee_holder)
            get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        fee = response.xpath("//div[contains(@data-course-audience, 'INT')]//div[contains(h3, '202') or contains(h3, "
                             "'fees')]/following-sibling::div").getall()
        int_fee_holder = []
        if fee:
            fee = ''.join(fee)
            int_fee = re.findall("\$\d*,?\d{3}", fee, re.M)
            if int_fee:
                for item in int_fee:
                    int_fee_holder.append(float(re.sub("[\$,]", "", item)))
        if int_fee_holder:
            course_item["internationalFeeAnnual"] = max(int_fee_holder)
            get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        learn = response.xpath("//div[@id='what-to-expect-tab']/div/div/div/*").getall()
        holder = []
        for index, item in enumerate(learn):
            if strip_tags(item) == '':
                pass
            elif not re.search('^<(p|o|u)', item) and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            course_item["whatLearn"] = strip_tags(''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        if course_item["courseName"].strip() == "University Certificate in Tertiary Preparation for Postgraduate " \
                                                "Studies":
            course_item["group"] = 4
            course_item["courseLevel"] = "Postgraduate"
            course_item["canonicalGroup"] = "PostgradAustralia"

        if response.request.url not in self.banned_urls and \
                not re.search("last offered 2019", course_item["courseName"], re.I):
            yield course_item
