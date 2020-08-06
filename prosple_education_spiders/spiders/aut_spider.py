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


class AutSpiderSpider(scrapy.Spider):
    name = 'aut_spider'
    allowed_domains = ['www.aut.ac.nz', 'aut.ac.nz']
    start_urls = ['https://www.aut.ac.nz/s/search.html?search_target=main&query=&collection=aut-ac-nz-meta-dev'
                  '&sitetheme=red&f.Tabs%7CT=Course&tab=Course&form=simple']
    banned_urls = ['https://www.aut.ac.nz/courses',
                   'https://www.aut.ac.nz/courses/doctor-of-philosophy/our-phd-students-and-alumni',
                   'https://www.aut.ac.nz/courses/certificate-of-proficiency']
    institution = 'Auckland University of Technology'
    uidPrefix = 'NZ-AUT-'

    campuses = {
        "North Campus": "53669",
        "City Campus": "53670",
        "South Campus": "53671",
        "Distance": "53672"
    }

    degrees = {
        "graduate certificate": "7",
        "postgraduate certificate": "7",
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
        boxes = response.xpath("//ol[@id='fb-results']/li[@class='clearfix courseItem']")

        for item in boxes:
            url = item.xpath(".//h3/a/@href").get()
            duration = item.xpath(".//td[contains(text(), 'Duration')]/following-sibling::*").get()
            location = item.xpath(".//td[contains(text(), 'Campus')]/following-sibling::*").get()
            intake = item.xpath(".//td[contains(text(), 'Starts')]/following-sibling::*").get()
            if url:
                yield response.follow(url, callback=self.course_parse,
                                      meta={'duration': duration, 'location': location, 'intake': intake})

        next_page = response.xpath("//a[@rel='next']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution

        course_name = response.xpath("//h1/text()").get()
        name = re.split(' - ', course_name.strip())
        holder = []
        for item in name:
            if re.search('bachelor|diploma|certificate|master', item):
                holder.insert(0, item.strip())
            else:
                holder.append(item)
        if holder:
            course_item.set_course_name(' - '.join(holder), self.uidPrefix)

        summary = response.xpath("//div[@class='intro']/*").get()
        if summary:
            course_item.set_summary(strip_tags(summary))

        overview = response.xpath("//div[@class='intro']/following-sibling::*[1]/*").getall()
        if overview:
            if summary:
                course_item["overview"] = strip_tags(summary + ''.join(overview), remove_all_tags=False)
            else:
                course_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False)

        course_code = response.xpath("//div[contains(text(), 'Programme code')]/following-sibling::div/text()").get()
        if course_code:
            course_item['courseCode'] = course_code.strip()

        entry = response.xpath("//*[contains(text(), 'Minimum entry requirements')]/following-sibling::*").getall()
        holder = []
        for item in entry:
            if re.search('^<p', item) or re.search('^<ul', item):
                holder.append(item)
            else:
                break
        if holder:
            course_item['entryRequirements'] = strip_tags(''.join(holder), remove_all_tags=False)

        career_link = response.xpath("//a[contains(*//text(), 'Career opportunities')]/@href").get()
        if career_link:
            career_link = re.sub('#', '', career_link)
            career_xpath1 = "//div[@id='" + career_link + "']/*"
            career_xpath2 = "//div[@id='" + career_link + "']//*[contains(@class, 'thumbnailTile')]/*"
            if response.xpath(career_xpath2).getall():
                career = response.xpath(career_xpath2).getall()
            else:
                career = response.xpath(career_xpath1).getall()
            course_item['careerPathways'] = strip_tags(''.join(career), remove_all_tags=False)

        location = response.meta['location']
        if location:
            study_holder = set()
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
                if campus == 'Distance':
                    study_holder.add('Online')
                else:
                    study_holder.add('In Person')
            if study_holder:
                course_item['modeOfStudy'] = '|'.join(study_holder)
            if campus_holder:
                course_item['campusNID'] = '|'.join(campus_holder)

        duration = response.meta['duration']
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
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

        intake = response.meta['intake']
        if intake:
            start_holder = []
            for month in self.months:
                if re.search(month, intake, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        dom_fee = response.xpath("//a[@title='Domestic fees']/following-sibling::span[1]").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)", dom_fee, re.M)
            if dom_fee:
                dom_fee = [float(''.join(x)) for x in dom_fee]
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//a[@title='International fees']/following-sibling::span[1]").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)", int_fee, re.M)
            if int_fee:
                int_fee = [float(''.join(x)) for x in int_fee]
                course_item["domesticFeeAnnual"] = max(int_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])

        course_item['courseName'] = course_name

        if course_item['sourceURL'] not in self.banned_urls:
            yield course_item
