# -*- coding: utf-8 -*-
# by: Johnel Bacani
# updated by: Christian Anasco

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


class ScSpider(scrapy.Spider):
    name = 'snc_spider'
    start_urls = [
        "https://stanleycollege.edu.au/vocational-courses/english-courses/",
        "https://stanleycollege.edu.au/vocational-courses/business/",
        "https://stanleycollege.edu.au/vocational-courses/hospitality/",
        "https://stanleycollege.edu.au/vocational-courses/commercial-cookery/",
        "https://stanleycollege.edu.au/vocational-courses/child-care-courses/",
        "https://stanleycollege.edu.au/vocational-courses/health-courses/",
        "https://stanleycollege.edu.au/vocational-courses/graduate-certificate/",
        "https://stanleycollege.edu.au/vocational-courses/graduate-diploma/",
        "https://stanleycollege.edu.au/vocational-courses/short-courses/",
        "https://stanleycollege.edu.au/vocational-courses/professional-year/",
        "https://stanleycollege.edu.au/vocational-courses/translation-interpreting/"
    ]
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    content_map = {
        'Course Duration': 'durationMinFull',
        'Study Modes': 'modeOfStudy',
        'Course Content': 'courseStructure',
        'Course Entry Requirements': 'entryRequirements',
        'Cost': 'domesticFeeTotal',
        'Intake Dates': 'startMonths',
        'Career Opportunities': 'careerPathways',
        'Recognition of Prior Learning': 'creditTransfer'
    }

    campuses = {
        "West Perth": "36610",
        "Mirrabooka": "36611",
        "James Street": "36365",
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

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.css("a.coursebtn.btn-hover::attr(href)").getall()
        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        institution = "Stanley College"
        uidPrefix = "AU-SNC-"

        # print("Hey")

        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_name = course_name.strip()
            if re.search("[A-Z0-9]+[A-Z0-9]+ ", course_name):
                course_code, course_name = re.split(
                    "\\s", course_name, maxsplit=1)
                course_name = course_name.replace("\n", " ")
                course_item.set_course_name(
                    course_name.strip(), self.uidPrefix)
                course_item["courseCode"] = course_code
            else:
                course_item.set_course_name(
                    course_name.strip(), self.uidPrefix)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by', 'for'])
        # Override assigned canonical group and group number
        course_item["canonicalGroup"] = "StudyPerth"
        course_item["group"] = 23

        course_item["uid"] = uidPrefix + course_item["courseName"]
        course_item["domesticApplyURL"] = response.request.url

        cricos = response.css("div.listdiv.cricos p").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        overview = response.xpath(
            "//div[@class='course-overviewsection']//div[@class='main-block']/*").getall()
        if overview:
            summary = [strip_tags(x) for x in overview if strip_tags(x) != '']
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        intake = response.css("div.listdiv.intake p").get()
        holder = []
        for item in self.months:
            if re.search(item, intake):
                holder.append(self.months[item])
        if holder:
            course_item["startMonths"] = "|".join(holder)

        duration = response.css("div.listdiv.duration p").get()
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
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(
                            duration_full[0][0])
                        self.get_period(
                            duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(
                            float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(
                            duration_full[1][1].lower(), course_item)

        study = response.xpath(
            "//*[@class='course-head' and text()='Study Modes']/following-sibling::*").getall()
        holder = set()
        if study:
            study = "".join(study)
            if re.search("face", study, re.I):
                holder.add("In Person")
            if re.search("online", study, re.I):
                holder.add("Online")
            if re.search("distance learning", study, re.I):
                holder.add("Online")
        if holder:
            course_item["modeOfStudy"] = "|".join(holder)

        dom_fee = response.css("div.listdiv.fees p").get()
        if dom_fee:
            dom_fee = re.findall(
                "\$\s?(\d*)[,\s]?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
                if "cricosCode" in course_item:
                    course_item["internationalFeeTotal"] = max(dom_fee)

        structure = response.xpath(
            "//*[@class='course-head' and text()='Course Content']/following-sibling::*").getall()
        if structure:
            course_item["courseStructure"] = strip_tags(
                ''.join(structure), remove_all_tags=False, remove_hyperlinks=True)

        entry = response.xpath(
            "//*[@class='course-head' and text()='Course Entry Requirements']/following-sibling::*").getall()
        if entry:
            course_item["entryRequirements"] = strip_tags(
                ''.join(entry), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//*[@class='course-head' and text()='Career Opportunities']/following-sibling::*").getall()
        if career:
            course_item["careerPathways"] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        credit = response.xpath(
            "//*[@class='course-head' and text()='Recognition of Prior Learning']/following-sibling::*").getall()
        if credit:
            course_item["creditTransfer"] = strip_tags(
                ''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        course_item["campusNID"] = "36610|36611|36365"

        yield course_item
