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


class RmiSpiderSpider(scrapy.Spider):
    name = 'rmi_spider'
    start_urls = ['https://www.rmit.edu.au/study-with-us']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "RMIT University"
    uidPrefix = "AU-RMI-"

    degrees = {
        "graduate certificate": "7",
        "online graduate certificate": "7",
        "graduate diploma": "8",
        "online graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "online master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "phd": "6",
        "certificate": "4",
        "vce": "9",
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
        "Point Cook": "11706",
        "Bundoora": "690",
        "Melbourne City": "689",
        "Brunswick": "691"
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

    # def parse(self, response):
    #     yield SplashRequest(response.request.url, callback=self.category_parse, args={'wait': 20})

    def parse(self, response):
        categories = response.xpath(
            "//article[@class='grid-list']//a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        sub = response.xpath("//div[contains(@class, 'iconlistsvg__content--row')]//a["
                             "@data-analytics-type='iconlink']/@href").getall()
        if sub:
            for item in sub:
                yield SplashRequest(response.urljoin(item), callback=self.link_parse, args={'wait': 20})
        else:
            yield SplashRequest(response.request.url, callback=self.link_parse, args={'wait': 20})

    def link_parse(self, response):
        courses = response.xpath(
            "//a[@data-analytics-type='program list']/@href").getall()

        for item in courses:
            yield response.follow(response.urljoin(item), callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_name = re.sub('\s-.*', '', course_name)
            course_item.set_course_name(
                strip_tags(course_name), self.uidPrefix)

        summary = response.xpath(
            "//*[contains(@class, 'shortdescription')]/*").getall()
        if summary:
            summary = [strip_tags(x) for x in summary]
            course_item.set_summary(' '.join(summary))

        overview = response.xpath(
            "//*[contains(@class, 'intro') and contains(@class, 'news--museo')]/following-sibling::*[contains(@class, 'cmp-text')]/*/*").getall()
        if overview:
            course_item["overview"] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath(
            "//*[@id='career']/ancestor::*[contains(@class, 'experiencefragment')]/following-sibling::*[contains(@class, 'cmp-text')]/*/*").getall()
        if career:
            career = [x for x in career if strip_tags(x) != '']
            course_item['careerPathways'] = strip_tags(
                ''.join(career), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Location')]/following-sibling::*").getall()
        holder = []
        if location:
            location = '|'.join(location)
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    holder.append(self.campuses[campus])
        if holder:
            course_item['campusNID'] = '|'.join(holder)

        duration = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Duration')]/following-sibling::*").getall()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall(
                "full.time (\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "part.time (\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
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

        intake = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Next intake')]/following-sibling::*").getall()
        if intake:
            intake = ''.join(intake)
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item['startMonths'] = '|'.join(start_holder)

        dom_fee = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Fees')]/following-sibling::*[contains(@class, 'qf-lcl-fee')]").get()
        if dom_fee:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Fees')]/following-sibling::*[contains(@class, 'qf-int-fee')]").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual",
                          "internationalFeeTotal", course_item)

        study = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Mode of study')]/following-sibling::*").getall()
        holder = []
        if study:
            study = "".join(study)
            if re.search("campus", study, re.I):
                holder.append("In Person")
            if re.search("online", study, re.I) or re.search("distance", study, re.I):
                holder.append("Online")
        if holder:
            course_item["modeOfStudy"] = "|".join(holder)

        atar = response.xpath(
            "//dt[contains(@class, 'qf--text--title') and contains(text(), 'Entry score')]/following-sibling::*").getall()
        if atar:
            atar = re.findall("(?<=ATAR\s)(\d*.?\d+)", atar, re.M)
            if atar:
                course_item["guaranteedEntryScore"] = float(atar[0])

        cricos = response.xpath(
            "//*[contains(@class, 'program-plan-listing')]").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item['cricosCode'] = ", ".join(set(cricos))
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        course_code = response.xpath(
            "//*[contains(text(), 'Program code:')]/following-sibling::node()").get()
        if course_code:
            course_item['courseCode'] = strip_tags(course_code)

        entry = response.xpath("//div[@class='MainSectionPad'][contains(*//h2/text(), "
                               "'Admissions')]/following-sibling::div[1]/div[contains(@class, "
                               "'extended-desc')]/*").getall()
        if entry:
            course_item['entryRequirements'] = strip_tags(''.join(entry), remove_all_tags=False,
                                                          remove_hyperlinks=True)

        credit = response.xpath(
            "//*[@id='credit-experiencefragment_c']//*[contains(@class, 'cmp-text')]/*/*").getall()
        if credit:
            credit = [x for x in credit if not re.search("^<a", x)]
            course_item['creditTransfer'] = strip_tags(
                ''.join(credit), remove_all_tags=False, remove_hyperlinks=True)

        course_item.set_sf_dt(self.degrees, degree_delims=[
                              'and', '/'], type_delims=['of', 'in', 'by'])

        if 'uid' in course_item and 'courseCode' in course_item:
            course_item['uid'] = course_item['uid'] + \
                '-' + course_item['courseCode']

        yield course_item
