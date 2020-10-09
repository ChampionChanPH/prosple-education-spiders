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


class HoiSpiderSpider(scrapy.Spider):
    name = 'hoi_spider'
    start_urls = ['https://holmesglen.edu.au/Courses/']
    institution = "Holmesglen Institute of TAFE"
    uidPrefix = "AU-HOI-"

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
        "victorian certificate": "9",
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
        "CIT Bruce": "55522",
        "CIT Fyshwick": "55523",
        "CIT Gungahlin": "55524",
        "CIT Reid": "55525",
        "CIT Tuggeranong": "55526"
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

    all_terms = get_terms()

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//div[@class='courseNavigation-courses']//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//section[@class='subHubListing']//a/@href").getall()

        for item in sub:
            yield response.follow(item, callback=self.link_parse)

    def link_parse(self, response):
        courses = response.xpath("//section[@data-wg='CourseTile']//a[@itemprop='url']/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='pageHeader-title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)
        sub_title = response.xpath("//span[@class='pageHeader-subTitle']/text()").get()
        if sub_title and 'uid' in course_item:
            sub_title = re.sub(' ', '-', sub_title.strip().lower())
            course_item['uid'] = course_item['uid'] + '-' + sub_title

        overview = response.xpath("//div[@class='courseDetailPage-secSubtitle']/*").getall()
        if overview:
            overview = ''.join(overview)
            course_item.set_summary(strip_tags(overview))
            course_item["overview"] = strip_tags(overview, False)

        course_code = response.xpath("//span[@class='pageHeader-codeTitle']/text()").get()
        if course_code:
            course_code = re.sub('Course Code', '', course_code)
            course_item['courseCode'] = course_code.strip()

        career = response.xpath("//*[contains(text(), 'Career opportunities')]/following-sibling::*").get()
        if career:
            course_item['careerPathways'] = strip_tags(career, False)

        learn = response.xpath("//*[contains(text(), 'Studying the') and contains(text(), "
                               "'at Holmesglen')]/following-sibling::*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), False)

        duration = response.xpath("//div[@id='courseTab-local']//*[contains(@id, 'lblLocalDuration')]").get()
        if duration:
            duration_full = re.findall("full.time.(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("part.time.(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                       duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        intake = response.xpath("//div[@id='courseTab-local']//*[contains(@id, 'lblLocalIntake')]").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        entry = response.xpath("//*[contains(text(), 'Entry requirements')]/following-sibling::*").getall()
        holder = []
        for item in entry:
            if not re.search('^<p', item):
                break
            else:
                holder.append(item)
        if holder:
            course_item['entryRequirements'] = ''.join(holder)

        credit = response.xpath("//*[contains(text(), 'Recognition of prior learning')]/following-sibling::*").getall()
        holder = []
        for item in credit:
            if not re.search('^<p', item):
                break
            else:
                holder.append(item)
        if holder:
            course_item['creditTransfer'] = ''.join(holder)

        location = response.xpath("//div[@id='courseTab-local']//*[contains(@id, 'lblLocalCampus')]").get()
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        international = response.xpath("//div[@id='courseTab-intl']").get()
        if international:
            if not re.search('not available for international students', international, re.I | re.M):
                course_item["internationalApps"] = 1

        dom_fee = response.xpath("//*[text()='Full Fee']/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            if dom_fee:
                course_item["domesticFeeAnnual"] = float(''.join(dom_fee[0]))
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//*[text()='Government subsidised']/following-sibling::*").get()
        if csp_fee:
            csp_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            if csp_fee:
                course_item["domesticSubFeeAnnual"] = float(''.join(csp_fee[0]))
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        int_fee = response.xpath("//div[@id='courseTab-intl']//*[contains(@id, 'lblIntlFees')]").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            if int_fee:
                course_item["internationalFeeAnnual"] = float(''.join(int_fee[0]))
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        update_matches(course_item, self.all_terms)

        yield course_item
