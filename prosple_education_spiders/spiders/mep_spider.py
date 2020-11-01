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


class MepSpiderSpider(scrapy.Spider):
    name = 'mep_spider'
    start_urls = ['https://www.melbournepolytechnic.edu.au/study/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Melbourne Polytechnic"
    uidPrefix = "AU-MEP-"

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
        "Heidelberg": "57293",
        "Epping": "57292",
        "Fairfield": "57291",
        "Preston": "57290",
        "Greensborough": "57294",
        "Prahran": "57295",
        "Collingwood": "57296",
        "Eden Park at Northern Lodge": "57297",
        "Yan Yean at Northern Lodge": "57299",
        "Online": "57300",
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
        categories = response.xpath("//a[contains(@class, 'home-search__browse-item')]/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//a[contains(@class, 'study-area__interests-item')]/@href").getall()

        for item in sub:
            yield SplashRequest(response.urljoin(item), callback=self.link_parse, args={'wait': 20})

    def link_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'mp-search-entry')]//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1").get()
        if course_name:
            course_item.set_course_name(strip_tags(course_name.strip()), self.uidPrefix)

        if 'courseName' in course_item:
            term = re.sub('(.*\s(in|of)\s)', '', course_item['courseName'], re.DOTALL)
            term = re.sub('\s[(-].*', '', term, re.DOTALL)
            term = re.sub(' ', '-', term.lower())
            url_term = re.split('/', course_item['sourceURL'])
            url_term = url_term[len(url_term) - 2]
        if not re.search(term, url_term):
            url_term = re.sub('(-local-students|-eveningflexible)', '', url_term)
            url_term = re.sub('-', ' ', url_term)
            course_item['courseName'] = course_item['courseName'] + ' - ' + make_proper(url_term)
            course_item.set_course_name(course_item['courseName'].strip(), self.uidPrefix)

        overview = response.xpath("//*[@class='course-overview__text']/*").getall()
        if overview:
            course_item["overview"] = strip_tags(''.join(overview), False, True)
            if len(overview) == 1:
                course_item.set_summary(strip_tags(overview[0]))
            elif re.search('<strong>', course_item["overview"], re.M):
                for index, item in enumerate(overview):
                    if re.search('^<h', item, re.M):
                        course_item.set_summary(strip_tags(overview[index + 1]))
                        break
            else:
                course_item.set_summary(strip_tags(overview[0]))

        if 'overview' not in course_item:
            overview = response.xpath(
                "//*[contains(text(), 'Suitable For') or contains(text(), 'Suitable for')]").get()
            if overview:
                overview2 = response.xpath("//*[contains(text(), 'Suitable For') or contains(text(), 'Suitable "
                                           "for')][1]/following-sibling::*").get()
                course_item["overview"] = strip_tags(overview + overview2, False, True)
                course_item.set_summary(strip_tags(overview + overview2))

        if 'overview' not in course_item:
            overview = response.xpath(
                "//*[@class='mp-short-course__heading'][text()='Overview']/following-sibling::*/*").getall()
            if overview:
                course_item["overview"] = strip_tags(''.join(overview), False, True)
                course_item.set_summary(strip_tags(''.join(overview)))

        if 'overview' not in course_item:
            overview = response.xpath("//*[@class='course-overview__text']").get()
            if overview:
                course_item["overview"] = strip_tags(overview, False, True)
                course_item.set_summary(strip_tags(overview))

        location = response.xpath("//*[@class='course-overview__infos']//*[@class='course-overview__info-title']["
                                  "contains(text(), 'Campus')]/following-sibling::*/*/text()").getall()
        if not location:
            location = response.xpath("//*[text()='LOCATION']/following-sibling::*/text()").getall()
        campus_holder = set()
        study_holder = set()
        if location:
            location = ', '.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if self.campuses['Online'] in campus_holder:
            study_holder.add('Online')
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            if len(campus_holder) == 1 and self.campuses['Online'] in campus_holder:
                pass
            else:
                study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        duration = response.xpath("//*[@class='course-overview__infos']//*[@class='course-overview__info-title']["
                                  "contains(text(), 'Duration')]/following-sibling::*").get()
        if not duration:
            duration = response.xpath("//*[text()='DURATION']/following-sibling::*/text()").get()
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
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        intake = response.xpath("//*[@class='course-overview__infos']//*[@class='course-overview__info-title']["
                                "contains(text(), 'Next Intake')]/following-sibling::*").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        holder = []
        career1 = response.xpath("//*[contains(text(), 'Where will this take me')]/following-sibling::text()").get()
        if career1:
            if strip_tags(career1) != '':
                holder.append(career1)
        career2 = response.xpath("//*[contains(text(), 'Where will this take me')]/following-sibling::ul/li").getall()
        if career2:
            holder.append('<ul>' + ''.join(career2) + '</ul>')
        if holder:
            course_item['careerPathways'] = strip_tags(''.join(holder), False)
        if 'careerPathways' not in course_item:
            career = response.xpath("//*[contains(text(), 'Course Outcomes:') or contains(text(), 'Course "
                                    "outcomes:')][1]/following-sibling::*").get()
            if career:
                course_item['careerPathways'] = strip_tags(career, False)

        credit = response.xpath("//*[contains(text(), 'Recognition of Prior Learning')]/following-sibling::*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(''.join(credit), False)

        entry = response.xpath("//*[text()='Requirements']/following-sibling::*[@data-type='local']").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), False)
        if 'entryRequirements' not in course_item:
            entry = response.xpath("//*[text()='Requirements']/following-sibling::text()").getall()
            entry = [strip_tags(x) for x in entry if strip_tags(x) != '']
            if entry:
                course_item['entryRequirements'] = strip_tags(' '.join(entry), False)

        learn = response.xpath("//*[contains(text(), 'Topics Covered:') or contains(text(), 'Topics covered:')]["
                               "1]/following-sibling::*").getall()
        holder = []
        for item in learn:
            if re.search(':', item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item['whatLearn'] = strip_tags(learn, False)

        course_code = response.xpath("//*[@class='course-hero__spacer'][contains(text(), 'Code:')]/text()").get()
        if course_code:
            course_code = re.findall('(?<=Code: ).*', course_code.strip(), re.DOTALL)
            if course_code:
                course_item['courseCode'] = course_code[0]
        if 'courseCode' not in course_item:
            course_code = response.xpath("//*[text()='CODE']/following-sibling::*/text()").get()
            if course_code:
                course_item['courseCode'] = course_code

        cricos = response.xpath("//*[@class='course-hero__spacer'][contains(text(), 'Cricos:')]/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1

        dom_fee = response.xpath("//*[@class='mp-course-fees__amount']").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
