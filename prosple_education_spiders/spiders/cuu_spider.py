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
    allowed_domains = ['www.acu.edu.au', 'study.curtin.edu.au', 'search.curtin.edu.au']
    start_urls = ['https://study.curtin.edu.au/search/?search_text=&study_type=course']
    institution = "Curtin University"
    uidPrefix = "AU-CUU-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "victorian certificate": "4",
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
        "Open Universities Australia": "573"
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
            study = item.xpath(".//div[@class='search-card__meta']//li[@aria-label='Availability']").get()
            if url:
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

        course_name = response.xpath("//dt[text()='Course']/following-sibling::dd/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath("//div[contains(@class, 'outline__lead')]/*/text()").get()
        if summary:
            course_item.set_summary(strip_tags(summary))

        overview = response.xpath("//div[contains(@class, 'outline__content')]/*").getall()
        if overview:
            course_item['overview'] = strip_tags(''.join(overview), False)

        atar = response.xpath("//dt[text()='Admission criteria']/following-sibling::dd/text()").get()
        if atar:
            guaranteed_atar = re.findall("(?<=Guaranteed ATAR\s)(\d*),?(\d+)", atar, re.M)
            minimum_atar = re.findall("(?<=Minimum ATAR\s)(\d*),?(\d+)", atar, re.M)
            if guaranteed_atar:
                course_item["guaranteedEntryScore"] = float(''.join(guaranteed_atar[0]))
            if minimum_atar:
                course_item["minScoreNextIntake"] = float(''.join(minimum_atar[0]))

        duration = response.xpath("//dt[contains(a/text(), 'Duration')]/following-sibling::dd").get()
        if duration and re.search(',', duration):
            duration_year = re.findall("(\d*\.?\d+)(?=\syear)", duration, re.I | re.M | re.DOTALL)
            duration_month = re.findall("(\d*\.?\d+)(?=\smonth)", duration, re.I | re.M | re.DOTALL)
            if duration_year and duration_month:
                duration_month = float(duration_month[0]) / 12
                course_item["durationMinFull"] = float(duration_year[0]) + duration_month
                course_item["teachingPeriod"] = 1
        else:
            if duration:
                duration_full = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?full.time)",
                    duration, re.I | re.M | re.DOTALL)
                duration_part = re.findall(
                    "(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?part.time)",
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

        location = response.xpath("//dt[text()='Location']/following-sibling::dd").get()
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
        if re.search('online', response.meta['study'], re.I | re.M):
            study_holder.append('Online')
            campus_holder.append(self.campuses['Open Universities Australia'])
        if campus_holder:
            study_holder.append('In Person')
            course_item['campusNID'] = '|'.join(campus_holder)
        if study_holder:
            course_item['modeOfStudy'] = '|'.join(study_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/', ','], type_delims=['of', 'in', 'by'])

        yield course_item
