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
                course_item[field_to_update] = float(
                    course_item[field_to_use]) * float(course_item["durationMinFull"])
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


class MurSpiderSpider(scrapy.Spider):
    name = 'mur_spider'
    start_urls = ['https://search.murdoch.edu.au/s/search.html?collection=mu-course-search&query=&sort=&resultView'
                  '=Grid&f.Study+level%7CcourseStudyLevel=&f.Study+type%7CstudyType=Course']
    institution = "Murdoch University"
    uidPrefix = "AU-MUR-"

    campuses = {
        "Rockingham": "683",
        "Perth": "680",
        "Mandurah": "682",
        "Singapore": "102280",
        "Dubai": "102282",
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "research masters with training": "12",
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
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

    term = {
        'Semester 1': '02',
        'Semester 2': '07',
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath(
            "//li[contains(@class, 'search-result-default')]//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

        next_page = response.xpath("//a[@rel='next']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath("//*[@class='sf-Long-text']/*").getall()
        if summary:
            summary = [strip_tags(x) for x in summary if strip_tags(x) != '']
            course_item.set_summary(' '.join(summary))

        overview = response.xpath(
            "//h2[@class='tab-title'][text()='Overview']/following-sibling::*[1]/*").getall()
        holder = []
        for item in overview:
            if re.search('<strong', item, flags=re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["overview"] = strip_tags(
                "".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//*[contains(*/text(), 'What you') and contains(*/text(), "
                               "'ll learn')]/following-sibling::*").getall()
        holder = []
        for item in learn:
            if re.search('<strong', item, flags=re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["whatLearn"] = strip_tags(
                "".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//*[contains(*/text(), 'Your career') or contains(*/text(), 'Your future "
                                "career')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if re.search('<strong', item, flags=re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags(
                "".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        course_code = response.xpath(
            "//h4[text()='Murdoch code']/following-sibling::*/text()").get()
        if course_code:
            course_item["courseCode"] = course_code

        cricos = response.xpath(
            "//h4[text()='CRICOS code']/following-sibling::*").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        atar = response.xpath(
            "//h4[text()='Selection rank']/following-sibling::*").get()
        if atar:
            atar = re.findall("\d+", atar, re.M)
            if atar:
                atar = [float(x) for x in atar]
                course_item["guaranteedEntryScore"] = max(atar)

        start = response.xpath(
            "//td[contains(@class, 'domestic-international') and contains(@class, 'active')]").getall()
        if start:
            start = ''.join(start)
            holder = []
            for item in self.term:
                if re.search(item, start, re.I | re.M):
                    holder.append(self.term[item])
            if holder:
                course_item['startMonths'] = '|'.join(holder)

        duration = response.xpath(
            "//h4[text()='Duration (years)']/following-sibling::*/text()").get()
        if duration:
            duration = re.findall("\d+", duration, re.M)
            if duration:
                duration = [float(x) for x in duration]
                course_item["durationMinFull"] = max(duration)
                course_item['teachingPeriod'] = 1

        location = response.xpath("//table[@class='offeringTable']").get()
        campus_holder = set()
        if location:
            for campus in self.campuses:
                if campus == 'Perth':
                    if re.search('Murdoch', location, re.I):
                        campus_holder.add(self.campuses[campus])
                elif re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
        if campus_holder:
            course_item['campusNID'] = '|'.join(campus_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/', '\+', ';'], type_delims=['of', 'in', 'by'])

        yield course_item
