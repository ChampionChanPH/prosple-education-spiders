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


class NorSpiderSpider(scrapy.Spider):
    name = 'nor_spider'
    start_urls = ['https://www.northregionaltafe.wa.edu.au/courses']
    banned_urls = []
    institution = 'North Regional TAFE'
    uidPrefix = 'AU-NOR-'

    campuses = {
        "Broome": "61730",
        "Derby": "61732",
        "Fitzroy Crossing": "61733",
        "Halls Creek": "61734",
        "Karratha": "61735",
        "Kununurra": "61736",
        "Minurmarghali Mia": "61737",
        "Newman": "61738",
        "Pundulmurra": "61739",
        "Tom Price": "61740",
        "Wyndham": "61741",
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "ampa master": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "foundation certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
        'postgraduate diploma': '8',
        'postgraduate certificate': '7',
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

    term = {
        'Semester 1': '02',
        'Semester 2': '07',
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//td[@class='c-course-title']/a")
        yield from response.follow_all(courses, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        course_code = response.xpath("//div[contains(@class, 'c-course-codes-section')]").get()
        if course_code:
            course_code = re.findall('(?<=National ID: )[A-Z0-9]*', course_code)
            if course_code:
                course_item['courseCode'] = course_code[0].strip()
        if course_name:
            if 'courseCode' in course_item:
                course_name = re.sub(course_item['courseCode'], '', course_name, re.I)
            course_name = re.sub('\(Master.*', '', course_name, re.DOTALL)
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//*[contains(@class, 'c-course-opening-section')]//*[@class='field-items']/*/*").getall()
        if overview:
            overview = [x for x in overview if strip_tags(x) != '']
        holder = []
        for index, item in enumerate(overview):
            if re.search('^<(p|u|o|h)', item):
                holder.append(item)
        if holder:
            if re.search('^Description', strip_tags(holder[0])):
                if len(holder) > 1:
                    summary = [strip_tags(x) for x in holder[1:]]
                    course_item.set_summary(' '.join(summary))
            elif re.search('[.?!]', strip_tags(holder[0]), re.M):
                summary = [strip_tags(x) for x in holder]
                course_item.set_summary(' '.join(summary))
            else:
                course_item.set_summary(strip_tags(holder[0]))
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//*[contains(@class, 'c-job-opportunities-free-text')]/*").getall()
        if career:
            course_item['careerPathways'] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath("//*[contains(@class, 'c-how-to-apply')]/*").getall()
        if apply:
            course_item['howToApply'] = strip_tags(''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//td[text()='Duration']/following-sibling::*/text()").get()
        if duration:
            duration_full = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\(?s?\)?\s+?full)",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\(?s?\)?\s+?part)",
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
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        location = response.xpath("//a[contains(@class, 'availability-title')]/following-sibling::*[1]//td[text("
                                  ")='Where']/following-sibling::*").getall()
        campus_holder = set()
        if location:
            location = '|'.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        study = response.xpath("//a[contains(@class, 'availability-title')]/following-sibling::*[1]//td[text("
                               ")='How']/following-sibling::*").getall()
        study_holder = set()
        if study:
            study = '|'.join(study)
            if re.search('on.?line', study, re.I | re.M | re.DOTALL):
                study_holder.add('Online')
            if re.search('distance', study, re.I | re.M | re.DOTALL):
                study_holder.add('Online')
            if re.search('paced|part|full|classroom|trainee|apprentice|onsite|work|campus|job|face', study,
                         re.I | re.M):
                study_holder.add('In Person')
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        dom_fee = response.xpath("//*[@class='c-fee-contenty']//td[1]").getall()
        if dom_fee:
            dom_fee = ''.join(dom_fee)
            dom_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        csp_fee = response.xpath("//*[@class='c-fee-contenty']//td[2]").getall()
        if csp_fee:
            csp_fee = ''.join(csp_fee)
            csp_fee = re.findall("\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", csp_fee, re.M)
            csp_fee = [float(''.join(x)) for x in csp_fee]
            if csp_fee:
                course_item["domesticSubFeeTotal"] = max(csp_fee)
                # get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        start = response.xpath("//*[@class='c-raw-data generic-accordion']/h3").getall()
        if start:
            start = ''.join(start)
            holder = []
            for item in self.term:
                if re.search(item, start, re.I | re.M):
                    holder.append(self.term[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        course_item['group'] = 141
        course_item['canonicalGroup'] = 'CareerStarter'

        yield course_item
