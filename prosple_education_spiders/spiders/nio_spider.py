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


class NioSpiderSpider(scrapy.Spider):
    name = 'nio_spider'
    start_urls = ['https://www.nioda.org.au/academic-programs/master-of-leadership-and-management-organisation'
                  '-dynamics/']
    institution = "The National Institute of Organisation Dynamics Australia (NIODA)"
    uidPrefix = "AU-NIO-"
    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Melbourne": "43679",
        "Sydney": "45896"
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
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//*[@class='et_pb_module_header']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        summary = response.xpath("//div[@class='et_pb_header_content_wrapper']/p/text()").get()
        if summary:
            course_item.set_summary(summary.strip())

        overview = response.xpath("//div[@class='et_pb_text_inner']/*[contains(*/text(), "
                                  "'OVERVIEW')]/following-sibling::*").getall()
        if overview:
            course_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath("//div[@class='et_pb_text_inner']/*[contains(text(), 'ADMISSION "
                               "REQUIREMENTS')]/following-sibling::*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//div[@class='et_pb_text_inner']/*[contains(text(), 'COURSE "
                               "CONTENT')]/following-sibling::*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath("//div[@class='et_pb_text_inner']/*[contains(text(), 'COURSE "
                                   "STRUCTURE')]/following-sibling::*").getall()
        if structure:
            course_item['courseStructure'] = strip_tags(''.join(structure), remove_all_tags=False,
                                                        remove_hyperlinks=True)

        apply = response.xpath("//div[@class='et_pb_text_inner']/*[contains(text(), 'HOW TO "
                               "APPLY')]/following-sibling::*").getall()
        if apply:
            course_item['howToApply'] = strip_tags(''.join(apply), remove_all_tags=False, remove_hyperlinks=True)

        fee = response.xpath("//div[@class='et_pb_text_inner']/*[contains(text(), 'FEES AND "
                             "COSTS')]/following-sibling::*").getall() 
        if fee:
            fee = "".join(fee)
            fee = re.findall(r"\$(\d*,?\d+) per year", fee, re.M | re.I)
            if fee:
                fee = float(re.sub(",", "", fee[0]))
                course_item["domesticFeeAnnual"] = fee

        location = response.xpath("//*[contains(text(), 'Locations')]/following-sibling::*").get()
        campus_holder = []
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if campus_holder:
            course_item["campusNID"] = "|".join(campus_holder)

        duration = response.xpath("//*[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration, re.M)
            if len(duration) == 1:
                course_item["durationMinPart"] = float(duration[0][0])
                self.get_period(duration[0][1], course_item)
            if len(duration) == 2:
                course_item["durationMinPart"] = min(float(duration[0][0]), float(duration[1][0]))
                course_item["durationMaxPart"] = max(float(duration[0][0]), float(duration[1][0]))
                self.get_period(duration[0][1], course_item)

        delivery = response.xpath("//*[contains(text(), 'Delivery Mode')]/following-sibling::*").getall()
        if delivery:
            delivery = ''.join(delivery)
            study_holder = []
            if re.search("face.to.face", delivery, re.M | re.I | re.DOTALL):
                study_holder.append("In Person")
            if re.search("online", delivery, re.M | re.I):
                study_holder.append("Online")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        course_code = response.xpath("//p[contains(strong/text(), 'Program code')]/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        course_item.set_sf_dt(self.degrees)

        yield course_item
