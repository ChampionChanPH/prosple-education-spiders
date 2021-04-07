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


class AnuCsppSpiderSpider(scrapy.Spider):
    name = 'anucspp_spider'
    allowed_domains = ['crawford.anu.edu.au', 'programsandcourses.anu.edu.au']
    start_urls = [
        'https://crawford.anu.edu.au/study/graduate-degrees',
        'https://crawford.anu.edu.au/executive-education/course/all'
    ]
    banned_urls = ['/study/graduate-degrees/phd-programs']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Crawford School of Public Policy"
    uidPrefix = "AU-ANU-CSPP-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Hobart": "43956",
        "Eveleigh": "43955"
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        if re.search('executive', response.request.url):
            courses = response.xpath(
                "//caption/following-sibling::tbody//strong/a/@href").getall()

            for item in courses:
                if item not in self.banned_urls:
                    yield response.follow(item, callback=self.short_parse)
        else:
            courses = response.xpath("//div[contains(@class, 'panel-display')]//a/@href").getall()

            for item in courses:
                if item not in self.banned_urls:
                    yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        course_name = response.xpath("//h1[@class='title']/text()").get()
        next_page = response.xpath("//a[contains(text(), 'degree program structure')]/@href").get()
        if not next_page:
            next_page = response.xpath("//a[contains(text(), 'View full degree details')]/@href").get()

        if next_page:
            yield SplashRequest(next_page, callback=self.course_parse, args={'wait': 10.0},
                                meta={'url': next_page, 'name': course_name})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta['url']

        course_name = response.meta['name']
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@id='introduction']/*").getall()
        relevant_degrees = response.xpath("//*[preceding-sibling::*[contains(text(), 'Relevant Degrees')]]").get()
        if relevant_degrees:
            relevant_degrees = '<br><strong>Relevant Degrees</strong><br>' + relevant_degrees
        else:
            relevant_degrees = ''
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview) + relevant_degrees, remove_all_tags=False,
                                                 remove_hyperlinks=True)

        career = response.xpath("//*[preceding-sibling::*[contains(text(), 'Career Options')]]").getall()
        if career:
            career = "".join(career)
            course_item["careerPathways"] = strip_tags(career, remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//*[preceding-sibling::*[contains(text(), 'Learning Outcomes')]]").get()
        if learn:
            course_item["whatLearn"] = strip_tags(learn, remove_all_tags=False, remove_hyperlinks=True)

        structure = response.xpath(
            "//div[@id='study']//*[preceding-sibling::*[contains(text(), 'Requirements')]]").getall()
        if structure:
            structure = "".join(structure)
            structure = re.sub("</?a[^]]*?>", "", structure, re.M | re.DOTALL | re.VERBOSE)
            course_item["courseStructure"] = strip_tags(structure, remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//span[contains(text(), 'Length')]/following-sibling::*/text()").get()
        if duration:
            duration = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration, re.M)
            if duration:
                if len(duration) > 0:
                    course_item["durationMinFull"] = float(duration[0][0])
                    self.get_period(duration[0][1], course_item)

        dom_fee = response.xpath("//dt[contains(text(), 'Annual indicative fee for domestic "
                                 "students')]/following-sibling::*").get()
        if dom_fee:
            dom_fee = re.findall("\$\d*,?\d+", dom_fee, re.M)
            if len(dom_fee) > 0:
                dom_fee = float(re.sub("[$,]", "", dom_fee[0]))
                course_item["domesticFeeAnnual"] = dom_fee
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//dt[contains(text(), 'Annual indicative fee for international "
                                 "students')]/following-sibling::*").get()
        if int_fee:
            int_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee) * 2
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        course_code = response.xpath("//*[preceding-sibling::*[contains(text(), 'Academic plan')]]/text()").get()
        if not course_code:
            course_code = response.xpath("//*[preceding-sibling::*[contains(text(), 'Specialisation code')]]/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        nominal = response.xpath("//*[preceding-sibling::*[contains(text(), 'Post Nominal')]]/text()").get()
        if nominal:
            if nominal.strip() != "":
                course_item["postNumerals"] = nominal.strip()

        cricos = response.xpath("//*[preceding-sibling::*[contains(text(), 'CRICOS')]]/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M | re.I)
            if len(cricos) > 0:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.meta['url']

        study_holder = []
        study = response.xpath("//*[preceding-sibling::*[contains(text(), 'Mode of delivery')]]/text()").getall()
        if study:
            study = "".join(study)
            if re.search("In Person", study, re.I | re.M):
                study_holder.append("In Person")
            if re.search("Online", study, re.I | re.M):
                study_holder.append("Online")
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        entry = response.xpath("//*[not(self::div)][preceding-sibling::*[contains(text(), 'Admission Requirements')]]").getall()
        if entry:
            entry = ''.join(entry)
            course_item["entryRequirements"] = strip_tags(entry, remove_all_tags=False, remove_hyperlinks=True)

        course_item["campusNID"] = '569'

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        yield course_item

    def short_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[contains(@class, 'field-name-field-feature-excerpt')]//p").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath(
            "//*[text()='Course overview']/following-sibling::*[1]//div[@class='field-item even']/*").getall()
        if learn:
            course_item['whatLearn'] = strip_tags(''.join(learn), remove_all_tags=False, remove_hyperlinks=True)

        presenter = response.xpath(
            "//*[text()='Course presenter(s)']/following-sibling::*[1]//div[@class='content']/*").getall()
        holder = []
        for item in presenter:
            if not re.search('<img', item):
                holder.append(item)
        if holder and 'overview' in course_item:
            course_item['overview'] += '<strong>Course presenter(s)</strong>'\
                                       + strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        info = response.xpath("//div[@class='field-label'][contains(text(), 'Cost')]/following-sibling::*").getall()
        if info:
            dom_fee = re.findall("\$(\d*),?(\d+)(\.\d\d)?", info, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeTotal"] = max(dom_fee)
                # get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
            start_holder = []
            for item in self.months:
                if re.search(item, info, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        study = response.xpath("//div[@class='field-label'][contains(text(), 'Venue')]/following-sibling::*").getall()
        if study:
            if re.search('online', info, re.I | re.M):
                course_item['modeOfStudy'] = 'Online'

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by", "Of"])

        course_item['degreeType'] = 'Short course or microcredential'

        yield course_item
