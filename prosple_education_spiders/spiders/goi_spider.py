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


class GoiSpiderSpider(scrapy.Spider):
    name = 'goi_spider'
    start_urls = ['https://www.gotafe.vic.edu.au/study/all-courses']
    institution = "Goulburn Ovens Institute of TAFE"
    uidPrefix = "AU-GOI-"

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
        "victorian certificate": "9",
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
        'Benalla - Samaria Road': '57669',
        'Seymour - Wallis Street': '57670',
        'Shepparton - Archer Street': '57671',
        'Shepparton - Fryers Street': '57672',
        'Shepparton - William Orr': '57673',
        'Wallan - High Street': '57674',
        'Wangaratta - Docker Street': '57675',
        'Wangaratta - Tone Road': '57676',
        'Online Campus': '57677',
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
        courses = response.xpath("//div[@class='course-search-result-title']/a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//h2/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        overview = response.xpath("//*[text()='Course Overview']/following-sibling::*").getall()
        if overview:
            course_item.set_summary(strip_tags(''.join(overview)))
            course_item["overview"] = strip_tags(''.join(overview), False)

        career = response.xpath("//*[text()='Career Pathways']/following-sibling::*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(''.join(career), False)

        duration = response.xpath("//div[*/text()='Course Length']/following-sibling::*/*//text()").getall()
        if duration:
            duration = ' '.join(duration)
            duration = re.sub('mth', 'month', duration)
            duration = re.sub('yr', 'year', duration)
        if duration:
            duration_full = re.findall("full.time.*?(\d*?\.?\d*?)?\s?-?\s?(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M |
                                       re.DOTALL)
            duration_part = re.findall("part.time.*?(\d*?\.?\d*?)?\s?-?\s?(\d*\.?\d+)(?=\s("
                                       "year|month|semester|trimester|quarter|week|day))", duration, re.I | re.M |
                                       re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][2].lower(), course_item)
            if duration_full:
                if duration_full[0][0] == '':
                    course_item["durationMinFull"] = float(duration_full[0][1])
                    self.get_period(duration_full[0][2].lower(), course_item)
                else:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][2].lower()] == course_item["teachingPeriod"]:
                    if duration_part[0][0] == '':
                        course_item["durationMinPart"] = float(duration_part[0][1])
                    else:
                        course_item["durationMinPart"] = min(float(duration_part[0][0]), float(duration_part[0][1]))
                        course_item["durationMaxPart"] = max(float(duration_part[0][0]), float(duration_part[0][1]))
                else:
                    if duration_part[0][0] == '':
                        course_item["durationMinPart"] = float(duration_part[0][1]) * course_item["teachingPeriod"] \
                                                         / self.teaching_periods[duration_part[0][2].lower()]
                    else:
                        course_item["durationMinPart"] = min(float(duration_part[0][0]), float(duration_part[0][1])) * \
                                                         course_item["teachingPeriod"] / \
                                                         self.teaching_periods[duration_part[0][2].lower()]
                        course_item["durationMaxPart"] = max(float(duration_part[0][0]), float(duration_part[0][1])) * \
                                                         course_item["teachingPeriod"] / \
                                                         self.teaching_periods[duration_part[0][2].lower()]
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

        dom_fee = response.xpath("//*[text()='Full Fee:']/following-sibling::*//text()").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//*[text()='Subsidised Standard:']/following-sibling::*//text()").get()
        if csp_fee:
            csp_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            csp_fee = [float(''.join(x)) for x in csp_fee]
            if csp_fee:
                course_item["domesticSubFeeTotal"] = max(csp_fee)
                # get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        location = response.xpath("//*[*/text()='Campuses'][*/circle]/following-sibling::*//text()").getall()
        campus_holder = set()
        study_holder = set()
        if location:
            location = [strip_tags(x) for x in location if strip_tags(x) != '']
            location = '|'.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if self.campuses['Online Campus'] in campus_holder:
            study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            if len(campus_holder) == 1 and self.campuses['Online'] in campus_holder:
                pass
            else:
                study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        study = response.xpath("//*[*/text()='Delivery Mode'][*/circle]/following-sibling::*//text()").getall()
        if study:
            study = [strip_tags(x) for x in study if strip_tags(x) != '']
            if study:
                course_item['modeOfStudy'] = '|'.join(study)

        entry = response.xpath("//div[contains(*/text(), 'Entry Requirements')]/following-sibling::*/*["
                               "@class='accordion-content']/*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(''.join(entry), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        credit = response.xpath("//div[contains(*/text(), 'Skills Recognition')]/following-sibling::*/*["
                                "@class='accordion-content']/*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath("//div[contains(*/text(), 'Enrolment')]/following-sibling::*/*["
                               "@class='accordion-content']/*").getall()
        if apply:
            course_item['howToApply'] = strip_tags(''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by", "Of"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
