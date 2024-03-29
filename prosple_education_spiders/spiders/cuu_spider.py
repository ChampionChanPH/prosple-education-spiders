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


class CuuSpider(scrapy.Spider):
    name = 'cuu_spider'
    start_urls = ['https://study.curtin.edu.au/search/?search_text=&study_type=course']
    institution = "Curtin University"
    uidPrefix = "AU-CUU-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "masters": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "victorian certificate": "4",
        "undergraduate certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
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
        "Curtin Perth": "572",
        "Curtin Murray Street": "571",
        "Curtin St Georges Terrace": "54872",
        "Curtin Kalgoorlie": "574",
        "Curtin Midland": "575",
        "Curtin University Malaysia": "577",
        "Curtin Singapore": "576",
        "Curtin University Dubai": "54873",
        "Curtin Mauritius": "578",
        "Open Universities Australia": "573",
        "Perth City": "54883"
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
        boxes = response.xpath("//div[@class='search-results__card-container']/div[@class='search-card']")

        for item in boxes:
            url = item.xpath(".//div[@class='search-card__title-wrap']//a/@href").get()
            category = item.xpath(
                ".//div[@class='search-card__title-wrap']/*[contains(@class, 'search-card__category')]/text()").get()
            study = item.xpath(".//div[@class='search-card__meta']//li[@aria-label='Availability']").get()
            if url and not re.search('major|specialisation|stream', category, re.I | re.M):
                yield response.follow(url, callback=self.course_parse, meta={'study': study})

        next_page = response.xpath("//div[@class='search-pagination__pages']/following-sibling::a["
                                   "@class='search-pagination__next']/@href").get()

        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//dt[text()='Course']/following-sibling::dd/text()").get()
        if not course_name:
            course_name = response.xpath("//dt[text()='MOOC']/following-sibling::dd/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath("//div[contains(@class, 'outline__lead')]/*/text()").get()
        if summary:
            course_item.set_summary(strip_tags(summary))

        overview = response.xpath("//div[contains(@class, 'outline__content')]/*").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search("^<p", item) and not re.search("^<ul", item) and not re.search("^<ol", item) \
                    and index != 0:
                break
            else:
                holder.append(item)
        if holder:
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
            if 'overviewSummary' not in course_item:
                summary = [strip_tags(x) for x in holder]
                course_item.set_summary(' '.join(summary))

        atar = response.xpath("//dt[text()='Admission criteria']/following-sibling::*").get()
        if atar:
            atar = re.findall("(?<=ATAR )(\d*),?(\d+)", atar, re.M)
            if atar:
                course_item["guaranteedEntryScore"] = float(''.join(atar[0]))

        cricos = response.xpath("//dt[text()='CRICOS']/following-sibling::dd/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ', '.join(cricos)
                course_item['internationalApps'] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_code = response.xpath("//p[contains(@class, 'offering-overview__hero__udc')]/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        learn = response.xpath(
            "//*[contains(text(), 'What you') and contains(text(), 'll learn')]/following-sibling::ul").get()
        if learn:
            course_item['whatLearn'] = strip_tags(learn, remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//dt[contains(*/text(), 'Duration')]/following-sibling::*").get()
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

        location = response.xpath("//dt[text()='Location']/following-sibling::*").get()
        campus_holder = set()
        study_holder = set()
        study = response.meta['study']
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.add(self.campuses[campus])
        if study and re.search('online', study, re.I | re.M):
            study_holder.add('Online')
        if 'courseName' in course_item:
            if re.search('OpenUnis', course_item['courseName'], re.I):
                campus_holder.add(self.campuses['Open Universities Australia'])
        if len(campus_holder) == 1 and self.campuses['Open Universities Australia'] in campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)
            study_holder.add('Online')
        elif campus_holder:
            study_holder.add('In Person')
            course_item['campusNID'] = '|'.join(campus_holder)
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        if 'courseName' in course_item:
            course_item.set_sf_dt(self.degrees, degree_delims=['and', '/', ','], type_delims=['of', 'in', 'by'])

            yield course_item
