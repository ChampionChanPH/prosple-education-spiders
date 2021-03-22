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


class VicSpiderSpider(scrapy.Spider):
    name = 'vic_spider'
    start_urls = ['https://www.vu.edu.au/search?collection=vu-meta&f.Tabs%7CcourseTab=Courses+%26+units&query'
                  '=!showall&f.Program+type|courses=Courses']
    institution = "Victoria University (VU)"
    uidPrefix = "AU-VIC-"

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

    campuses = {
        "Werribee": "841",
        "Sunshine": "842",
        "St Albans": "847",
        "Industry": "845",
        "Footscray Nicholson": "849",
        "City Flinders": "844",
        "City Queen": "848",
        "Footscray Park": "840",
        "Sydney": "850",
        "Melbourne": "851",
        "City King St": "843"
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
        courses = response.xpath("//div[contains(@class, 'search-layout__search-results')]//li[contains(@class, "
                                 "'search-result-course')]/@data-fb-result").getall()
        for item in courses:
            if not re.search('online.vu.edu', item, re.M | re.DOTALL):
                if re.search('shortcourses', item, re.M):
                    yield response.follow(item, callback=self.short_parse)
                else:
                    yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//li[@class='next']/a/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1[@class='page-header']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//div[contains(@class, 'field-name-field-unit-code')]//div[@class='field-item "
                                     "even ']/text()").get()
        if not course_code:
            course_code = response.xpath("//div[@class='key-summary-content']/div[contains(div/div/text(), 'Course "
                                         "code')]/following-sibling::*/div/div/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        summary = response.xpath("//p[@class='paragraph--lead']/text()").get()

        overview = response.xpath("//section[@id='description']//div[@class='field-item even ']/*").getall()
        if not overview:
            overview = response.xpath("//div[contains(@class, 'paragraphs-item-page-intro')]//div[contains(@class, "
                                      "'field-type-text-with-summary')]//div[@class='field-item even ']/*").getall()
        if not overview:
            overview = response.xpath(
                "//div[@id='overview']//p[@class='paragraph--lead']/following-sibling::*").getall()
        if not overview:
            overview = response.xpath("//div[@id='overview']//div[contains(@class, 'col-md-7')]/*").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search('^<(p|u|o)', item) and index != 0 and index != 1:
                break
            elif re.search('^<(p|u|o)', item) and not re.search('<img', item):
                holder.append(item)
        if holder:
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
            summary_holder = []
            if summary:
                summary_holder.append(summary)
            summary_holder.extend([strip_tags(x) for x in holder])
            if summary_holder:
                course_item.set_summary(' '.join(summary_holder))

        cricos = response.xpath("//div[contains(@class, 'field-name-vucrs-cricos-code')]//div[@class='field-item even "
                                "']").get()
        if not cricos:
            cricos = response.xpath("//div[@class='key-summary-content']/div[contains(div/div/text(), 'CRICOS "
                                    "code')]/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(set(cricos))
                course_item["internationalApps"] = 1

        duration = response.xpath("//div[@class='course-essential-block']//*[contains(text(), "
                                  "'Duration')]/following-sibling::*").get()
        if not duration:
            duration = response.xpath("//div[@class='key-summary-content']/div[contains(div/div/text(), "
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
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 1:
                    #     course_item["durationMinFull"] = float(duration_full[0][0])
                    #     self.get_period(duration_full[0][1].lower(), course_item)
                    # if len(duration_full) == 2:
                    #     course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                    #     self.get_period(duration_full[1][1].lower(), course_item)

        location = response.xpath("//div[@class='course-essential-block']//*[contains(text(), "
                                  "'Location')]/following-sibling::*").get()
        if not location:
            location = response.xpath("//div[@class='key-summary-content']/div[contains(div/div/text(), "
                                      "'Location')]/following-sibling::*").get()
        campus_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        study = response.xpath("//div[@class='course-essential-block']//*[contains(text(), 'Delivery "
                               "mode')]/following-sibling::*").get()
        holder = set()
        if study:
            if re.search('face', study, re.I | re.M | re.DOTALL):
                holder.add('In Person')
            if re.search('online', study, re.I | re.M | re.DOTALL):
                holder.add('Online')
            if re.search('blended', study, re.I | re.M | re.DOTALL):
                holder.add('In Person')
                holder.add('Online')
        if holder:
            course_item['modeOfStudy'] = '|'.join(holder)

        intake = response.xpath("//div[@class='course-essential-block']//*[contains(text(), 'Start "
                                "date')]/following-sibling::*").get()
        if not intake:
            intake = response.xpath("//div[@class='key-summary-content']/div[contains(div/div/text(), "
                                    "'Intakes')]/following-sibling::*").get()
        if intake:
            holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        career = response.xpath("//section[@id='careers']//div[@class='field-item even ']/*").getall()
        if career:
            career = [x for x in career if strip_tags(x) != '']
            course_item["careerPathways"] = strip_tags(''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath("//div[@class='completion-rules']//div[@class='field-item even ']/*").getall()
        if structure:
            structure = [x for x in structure if strip_tags(x) != '']
            course_item['courseStructure'] = strip_tags(''.join(structure), remove_all_tags=False,
                                                        remove_hyperlinks=True)

        apply = response.xpath("//div[@class='before-you-apply']/*").getall()
        if apply:
            apply = [x for x in apply if strip_tags(x) != '']
            course_item["howToApply"] = strip_tags(''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath("//div[@id='accordion-pathways-credit-content']/*").getall()
        if credit:
            credit = [x for x in credit if strip_tags(x) != '']
            course_item["creditTransfer"] = strip_tags(''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        # course_item["domesticApplyURL"] = response.request.url
        # course_item["internationalApplyURL"] = response.request.url

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by", "Of"])

        international_link = response.xpath(
            "//div[@class='course-link']//div[contains(@class, 'non-residents')]//a/@href").get()
        if international_link:
            yield response.follow(international_link, callback=self.international_parse, meta={'item': course_item})
        else:
            yield course_item

    def international_parse(self, response):
        course_item = response.meta['item']

        int_fee = response.xpath("//div[@class='course-essential-block']//*[contains(text(), "
                                 "'Fees')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee) * 2
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        yield course_item

    def short_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/div[contains(@class, 'ax-course-details')]/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = response.xpath("//h2/div[contains(@class, 'ax-course-details')]/text()").get()
        if course_code:
            course_code = re.findall('(?<=COURSE CODE:.)[A-Z]+', course_code, re.DOTALL)
            course_item["courseCode"] = ', '.join(course_code)

        duration = response.xpath(
            "//div[contains(@class, 'ax-course-details')]//div[contains(@class, 'duration')]").get()
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
        if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
            course_item["durationMinFull"] = 1
            course_item['teachingPeriod'] = 365

        dom_fee = response.xpath("//div[contains(@class, 'ax-course-details')]//div[contains(@class, 'cost')]//*["
                                 "@class='sam-span']/text()").get()
        if dom_fee:
            try:
                course_item["domesticFeeAnnual"] = float(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
            except ValueError:
                pass

        location = response.xpath("//div[contains(@class, 'ax-course-details')]//div[contains(@class, 'method')]").get()
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

        intake = response.xpath("//div[@class='date']").get()
        if intake:
            holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    holder.append(self.months[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        holder = response.xpath("//div[@class='ax-course-introduction']").getall()
        if len(holder) == 3:
            learn, overview, entry = holder
            if learn:
                course_item['whatLearn'] = strip_tags(learn, remove_all_tags=False, remove_hyperlinks=True)
            if overview:
                course_item['overview'] = strip_tags(overview, remove_all_tags=False, remove_hyperlinks=True)
                summary = strip_tags(overview)
                summary = re.sub('\s+', ' ', summary, re.M)
                course_item['overviewSummary'] = summary
            if entry:
                course_item['entryRequirements'] = strip_tags(entry, remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by", "Of"])

        yield course_item
