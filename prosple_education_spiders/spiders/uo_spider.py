# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by: Christian Anasco on 3rd May, 2021

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


class UoSpiderSpider(scrapy.Spider):
    name = 'uo_spider'
    start_urls = ['https://www.otago.ac.nz/courses/qualifications/apply/index.html']

    institution = "University of Otago"
    uidPrefix = "NZ-UO-"

    degrees = {
        "postgraduate certificate": "7",
        "graduate certificate": "7",
        "postgraduate diploma": "8",
        "graduate diploma": "8",
        "diploma for graduates": "8",
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

    def parse(self, response):
        courses = response.xpath("//h3//following-sibling::*[1]//li/a/@href").getall()

        for item in set(courses):
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//div[@id='title']//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        course_code = re.findall("\((.*)\)", course_name)
        if course_code:
            course_item["courseCode"] = course_code[0]

        overview = response.xpath("//h2[contains(text(), 'About') or text()='Overview']/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(overview):
            if re.search('^<(p|u|o)', item):
                holder.append(item)
            elif index == 0:
                pass
            else:
                break
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath("//*[text()='Cross Credits']/following-sibling::*").getall()
        if credit:
            course_item['creditTransfer'] = strip_tags(''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//*[text()='Admission to the Programme' or text()='Prerequisites, Corequisites and "
                               "Restrictions']/following-sibling::*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(credit), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/', ','], type_delims=['of', 'in', 'by'])

        course_item["group"] = 2
        course_item["canonicalGroup"] = "GradNewZealand"
        course_item["campusNID"] = "48009"

        yield course_item
