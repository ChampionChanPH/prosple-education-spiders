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


class TasSpiderSpider(scrapy.Spider):
    name = 'tas_spider'
    start_urls = ['https://www.tafesa.edu.au/courses/']
    institution = "TAFE SA"
    uidPrefix = "AU-TAS-"

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
        "certificate i program": "4",
        "certificate ii program": "4",
        "certificate iii program": "4",
        "certificate iv program": "4",
        "advanced diploma": "5",
        "advanced diploma program": "5",
        "diploma": "5",
        "diploma program": "5",
        "dual diploma program": "5",
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
        "Adelaide City": "56511",
        "Adelaide College of the Arts": "56512",
        "Elizabeth": "56513",
        "Gilles Plains": "56514",
        "Noarlunga": "56515",
        "Regency Park": "56516",
        "Salisbury": "56517",
        "Tonsley": "56518",
        "Urrbrae": "56519",
        "Mount Barker": "56520",
        "Victor Harbor": "56521",
        "Barossa Valley": "56522",
        "Berri": "56523",
        "Murray Bridge": "56524",
        "Coober Pedy": "56525",
        "Port Augusta": "56526",
        "Roxby Downs": "56527",
        "Mount Gambier": "56528",
        "Ceduna": "56529",
        "Port Lincoln": "56530",
        "Whyalla": "56532",
        "Wudinna": "56533",
        "Kadina": "56534",
        "Narungga": "56535",
        "Port Pirie": "56536",
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
        categories = response.xpath("//*[contains(text(), 'Course Areas')]/following-sibling::*["
                                    "@class='grid_mainContent']//ul//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[@class='areas_of_study']//a/@href").getall()

        for item in sub:
            yield response.follow(item, callback=self.link_parse)

    def link_parse(self, response):
        courses = response.xpath("//div[contains(@class, 'study_area_course_list')]//tr//a/@href").getall()
        courses = set([re.sub('(?<=aspx).*', '', x) for x in courses])

        for item in courses:
            if re.search('/xml/', item):
                yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='cp_title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//*[@id='CourseDescription']").getall()
        if overview:
            overview = ''.join(overview)
            course_item.set_summary(strip_tags(overview))
            course_item["overview"] = strip_tags(overview, False)

        career = response.xpath("//h3[contains(text(), 'Employment Outcomes')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if re.search('^<p', item) or re.search('^<ul', item) or re.search('^<ol', item):
                holder.append(item)
            else:
                break
        if holder:
            course_item["careerPathways"] = strip_tags(''.join(holder), False)

        course_code = response.xpath("//*[@class='course-codes']/*[@class='tafesa-code']/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()
            course_item['uid'] = course_item['uid'] + '-' + course_item['courseCode']

        duration = response.xpath("//div[contains(@class, 'cp_cell') and contains(text(), 'Up to')]").get()
        if duration:
            duration = re.sub('\xa0', ' ', duration)
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
                                           duration, re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        entry = response.xpath("//*[contains(text(), 'Course Admission Requirements')]/following-sibling::*").getall()
        if entry:
            entry = [x for x in entry if strip_tags(x).strip() != '']
            course_item["entryRequirements"] = strip_tags(''.join(entry), False)

        dom_fee = response.xpath("//div[contains(text(), 'Full Fee') or contains(*/text(), 'Full "
                                 "Fee')]/following-sibling::*[last()]").get()
        if dom_fee:
            dom_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            if dom_fee:
                dom_fee = [float(''.join(x)) for x in dom_fee]
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//div[contains(text(), 'Subsidised') or contains(*/text(), "
                                 "'Subsidised')]/following-sibling::*[last()]").get()
        if csp_fee:
            csp_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", csp_fee, re.M)
            if csp_fee:
                csp_fee = [float(''.join(x)) for x in csp_fee]
                course_item["domesticSubFeeAnnual"] = max(csp_fee)
                get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        location = response.xpath("//a[contains(@title, 'campus information')]/text()").getall()
        campus_holder = set()
        study_holder = set()
        if location:
            location = ''.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        int_link = response.xpath("//div[@class='intake_tab-wrapper']/a[text()='International']/@href").get()
        if int_link:
            yield response.follow(int_link, callback=self.international_parse, meta={'item': course_item})
        elif re.search('/in/', course_item['sourceURL']):
            yield response.follow(course_item['sourceURL'], callback=self.international_parse, meta={'item': course_item})
        else:
            yield course_item

    @staticmethod
    def international_parse(response):
        course_item = response.meta['item']

        cricos = response.xpath("//*[@class='course-codes']/*[@class='cricos-code']/text()").get()
        if cricos:
            course_item['cricosCode'] = cricos.strip()
            course_item["internationalApps"] = 1

        int_fee = response.xpath("//div[@class='cp_cell'][contains(text(), 'Total Fees')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$\s?(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            if int_fee:
                int_fee = [float(''.join(x)) for x in int_fee]
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        yield course_item
