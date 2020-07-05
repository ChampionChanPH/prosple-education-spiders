# -*- coding: utf-8 -*-
# by Christian Anasco
# having difficulties getting the annual fee for courses

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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


class MonSpiderSpider(scrapy.Spider):
    name = 'mon_spider'
    allowed_domains = ['mon3-search.clients.squiz.net', 'www.monash.edu', 'monash.edu']
    start_urls = ['https://www.monash.edu/study/courses/find-a-course?f.Tabs%7CcourseTab=Undergraduate&f'
                  '.InterestAreas%7CcourseInterestAreas=',
                  'https://www.monash.edu/study/courses/find-a-course?f.Tabs%7CcourseTab=Graduate&f.InterestAreas'
                  '%7CcourseInterestAreas=',
                  'https://www.monash.edu/study/courses/find-a-course?f.Tabs%7CcourseTab=Double+degrees&f'
                  '.InterestAreas%7CcourseInterestAreas=',
                  'https://www.monash.edu/study/courses/find-a-course?f.Tabs%7CcourseTab=Professional+development&f'
                  '.InterestAreas%7CcourseInterestAreas=']
    banned_urls = []
    courses = []
    institution = "Monash University"
    uidPrefix = "AU-MON-"

    campuses = {
        "The Alfred": "677",
        "Peninsula": "660",
        "Prince Henry's Institute - MMC Clayton": "665",
        "Howard Florey Institute - Parkville": "672",
        "Melbourne City": "679",
        "Melbourne": "667",
        "Australia": "661",
        "Monash Medical Centre - Clayton": "664",
        "Mental Health Research Institute - Parkville": "673",
        "Jakarta International College": "11783",
        "Malaysia": "659",
        "Southbank": "669",
        "Singapore": "675",
        "Off-campus": "657",
        "Notting Hill": "670",
        "Murdoch Children's Research": "674",
        "Indonesia - Surabaya": "11782",
        "Hong Kong": "676",
        "Gippsland": "658",
        "Colombo": "11781",
        "Box Hill Hospital": "666",
        "Bendigo": "671",
        "Alfred Hospital": "662",
        "Clayton": "656",
        "Caulfield": "655",
        "Parkville": "668"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "phd": "6",
        "advanced certificate": "7",
        "certificate": "4",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
        "accam - australian certificate": "13",
        "juris doctor": "10"
    }

    degree_split = {
        "Bachelor degree": {'begin': 'Bachelor of ', 'end': ''},
        "Short course": {'begin': '', 'end': ''},
        "Tailored program": {'begin': '', 'end': ''},
        "Single-day program": {'begin': '', 'end': ''},
        "Master degree": {'begin': 'Master of ', 'end': ''},
        "Expert master degree": {'begin': 'Expert Master of ', 'end': ''},
        "Graduate certificate": {'begin': 'Graduate Certificate in ', 'end': ''},
        "Professional entry master degree": {'begin': 'Master of ', 'end': ''},
        "Doctorate": {'begin': 'Doctor of ', 'end': ''},
        "PhD": {'begin': 'Doctor of ', 'end': ''},
        "Research master degree": {'begin': 'Master of ', 'end': ' (Research)'},
        "Graduate diploma": {'begin': 'Graduate Diploma of ', 'end': ''},
        "Executive master degree": {'begin': 'Executive Master of ', 'end': ''},
        "Bachelor degree (honours)": {'begin': 'Bachelor of ', 'end': ' (Honours)'},
        "Diploma": {'begin': 'Diploma of ', 'end': ''},
        "Bachelor degree (honours year)": {'begin': 'Bachelor of ', 'end': ' (Honours)'},
        "Seminar": {'begin': '', 'end': ''},
        "Enabling course": {'begin': '', 'end': ''},
        "Diploma (available for concurrent study alongside your degree)": {'begin': 'Diploma of ', 'end': ''}
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
        boxes = response.xpath("//div[contains(@class, 'search-results')]/div[contains(@class, "
                               "'box-featured__wrapper')]")
        # for item in boxes:
        #     url = item.xpath(".//div[contains(@class, 'box-featured__blurb')]//h2[contains(@class, "
        #                      "'box-featured__heading')]/a/@href").get()
        #     degree = item.xpath(".//div[contains(@class, 'box-featured__blurb')]//span[contains(@class, "
        #                         "'box-featured__level')]/text()").get()
        #     yield response.follow(url, callback=self.course_parse, meta={'degree': degree})

        url = "https://www.monash.edu/study/courses/find-a-course/2020/juris-doctor-l6005?domestic=true"
        degree = "Professional entry master degree"
        yield response.follow(url, callback=self.course_parse, meta={'degree': degree})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.xpath("//h1/text()").get()
        if not name:
            name = response.xpath("//strong[@class='h1']/text()").get()
        if name:
            split_name = name.split("-")
            name = split_name[0]
            if len(split_name) > 1:
                code = split_name[1]
                course_item["courseCode"] = code.strip()
            name = name.strip()
        degree = str(response.meta['degree'])
        if degree:
            degree = degree.strip()
            degree = degree.split("/")
        if response.meta['degree'] not in ["Short course", "Tailored program", "Single-day program", "Seminar",
                                           "Enabling course"]:
            name = name.split(" and ")
        else:
            name = [name]
        holder = []
        for name, degree in zip(name, degree):
            if name == "Juris Doctor":
                holder.append(name)
            else:
                holder.append(self.degree_split[degree]["begin"] + name + self.degree_split[degree]["end"])
        if holder:
            course_item.set_course_name(" / ".join(holder), self.uidPrefix)

        overview = response.xpath(
            "//div[contains(@class, 'course-page__overview-panel')]//*[self::p or self::ul]").getall()
        if overview:
            course_item.set_summary(strip_tags(overview[0]))
            course_item["overview"] = strip_tags("".join(overview), False)

        location = response.xpath("//th[contains(*/text(), 'Location')]/following-sibling::*").get()
        if not location:
            location = response.xpath("//p[@class='course-info-box__field'][contains(*/text(), 'Location')]").get()
        if location:
            campus_holder = []
            for campus in self.campuses:
                if campus == "Parkville":
                    if re.search("(?<!-\s)Parkville", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif campus == "Clayton":
                    if re.search("(?<!-\s)Clayton", location, re.I | re.M) and \
                            re.search("(?<!MMC\s)Clayton", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif campus == "Melbourne":
                    if re.search("Melbourne(?!\sCity)", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)
            study_holder = set()
            if len(campus_holder) == 1:
                if re.search("online", location, re.I | re.M):
                    study_holder.add("Online")
                else:
                    study_holder.add("In Person")
            if len(campus_holder) > 1:
                if re.search("online", location, re.I | re.M):
                    study_holder.add("Online")
                study_holder.add("In Person")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)

        duration = response.xpath("//th[contains(*/text(), 'Duration')]/following-sibling::*").get()
        if not duration:
            duration = response.xpath("//p[@class='course-info-box__field'][contains(*/text(), 'Length')]").get()
        if duration:
            duration = re.sub("\r\n", "", duration)
            duration = re.sub("\s+", " ", duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?full.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\s\(?part.time)",
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
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        intake = response.xpath("//th[contains(*/text(), 'Start date')]/following-sibling::*").get()
        if not intake:
            intake = response.xpath("//p[@class='course-info-box__field'][contains(*/text(), 'Date')]").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.I | re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        csp_fee = response.xpath(
            "//*[contains(text(), 'Commonwealth supported place (CSP)')]/following-sibling::*").getall()
        if csp_fee:
            holder = []
            for item in csp_fee:
                if re.search("^<h", item, re.M):
                    break
                else:
                    holder.append(item)
            if holder:
                holder = "".join(holder)
                holder = re.findall("\$(\d*),?(\d+)", holder, re.M)
                if holder:
                    course_item["domesticSubFeeAnnual"] = float(holder[0][0] + holder[0][1])
                    get_total("domesticSubFeeAnnual", "domesticSubFeeTotal", course_item)

        dom_fee = response.xpath(
            "//*[contains(text(), 'Full fee')]/following-sibling::*").getall()
        if dom_fee:
            holder = []
            for item in dom_fee:
                if not re.search("^<p", item, re.M):
                    break
                else:
                    holder.append(item)
            if holder:
                holder = "".join(holder)
                holder = re.findall("\$(\d*),?(\d+)", holder, re.M)
                if holder:
                    course_item["domesticFeeAnnual"] = float(holder[0][0] + holder[0][1])
                    get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        cost = response.xpath("//p[@class='course-info-box__field'][contains(*/text(), 'Cost')]").get()
        if cost:
            holder = re.findall("\$(\d*),?(\d+)", cost, re.M)
            if holder:
                course_item["domesticFeeTotal"] = float(holder[0][0] + holder[0][1])

        course_item.set_sf_dt(self.degrees)

        int_link = re.sub("domestic", "international", course_item["sourceURL"])

        if int_link:
            yield response.follow(int_link, callback=self.int_parse, meta={'item': course_item})
        else:
            yield course_item

    def int_parse(self, response):
        course_item = response.meta['item']

        int_fee = response.xpath(
            "//*[contains(text(), 'International fee')]/following-sibling::*").getall()
        if int_fee:
            holder = []
            for item in int_fee:
                if not re.search("^<p", item, re.M):
                    break
                else:
                    holder.append(item)
            if holder:
                holder = "".join(holder)
                holder = re.findall("\$(\d*),?(\d+)", holder, re.M)
                if holder:
                    course_item["internationalFeeAnnual"] = float(holder[0][0] + holder[0][1])
                    get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        cricos = response.xpath("//*[contains(text(), 'CRICOS code')]").getall()
        if cricos:
            cricos = "".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)

        course_item["internationalApps"] = 1
        course_item["internationalApplyURL"] = course_item["sourceURL"]

        yield course_item