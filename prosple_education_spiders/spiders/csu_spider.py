# -*- coding: utf-8 -*-
# by Christian Anasco
# put on hold, had issues with javascript

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


class CsuSpiderSpider(scrapy.Spider):
    name = 'csu_spider'
    allowed_domains = ['study.csu.edu.au']
    start_urls = ['https://study.csu.edu.au/courses/all']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "Charles Sturt University"
    uidPrefix = "AU-CSU-"

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "postgraduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
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
        "Holmesglen": "540",
        "Bathurst": "527",
        "Uni Wide": "529",
        "Port Macquarie": "532",
        "Dubbo": "530",
        "Canberra": "528",
        "Orange": "539",
        "CSU Study Centre Brisbane": "534",
        "Brisbane": "538",
        "CSU Study Centre Melbourne": "531",
        "Melbourne": "533",
        "Northern Sydney Institute": "535",
        "Sydney": "536",
        "Albury-Wodonga": "525",
        "Albury": "537",
        "Wagga Wagga": "526"
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

    sessions = {
        "Session 1 2020": "03",
        "Session 2 2020": "07"
    }

    def parse(self, response):
        courses = response.xpath("//div[@id='all-courses-list']//a/@href").getall()

        # courses = [
        #     "https://study.csu.edu.au/courses/business/bachelor-communication-advertising-bachelor-business-marketing",
        #     "https://study.csu.edu.au/courses/psychology/bachelor-psychology",
        #     "https://study.csu.edu.au/courses/teaching-education/master-adult-vocational-education"]
        for course in courses:
            yield SplashRequest(course, callback=self.course_parse, args={"wait": 20}, meta={'url': course})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["published"] = 1
        course_item["institution"] = self.institution

        # course_item["domesticApplyURL"] = response.meta['url']

        course_name = response.xpath("//div[@id='banner-heading']/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.css(".overview-text .row p.intro-blurb::text").get()
        if overview:
            course_item["overview"] = cleanspace(overview)
            course_item.set_summary(course_item["overview"])

        study = response.xpath("//*[text()='Study mode']/following-sibling::*").get()
        study_holder = []
        if len(study) > 0:
            if re.search(r"on campus", study, re.I | re.M):
                study_holder.append("In Person")
            if re.search(r"online", study, re.I | re.M):
                study_holder.append("Online")
        if len(study_holder) > 0:
            course_item["modeOfStudy"] = "|".join(study_holder)

        location = response.xpath("//*[text()='Campus locations']/following-sibling::*").get()
        campus_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)

        career = response.xpath("//*[text()='Career opportunities']/following-sibling::*").get()
        if career is not None:
            course_item["careerPathways"] = strip_tags(career, False)

        c_atar = response.xpath("//*[contains(@id, 'cYear-atar')]").get()
        f_atar = response.xpath("//*[contains(@id, 'fYear-atar')]").get()
        if re.search(r"display: none;", c_atar, re.M):
            atar = f_atar
        else:
            atar = c_atar
        if atar is not None:
            score = re.findall(r"(?<=Minimum Selection Rank required for consideration: )\d*\.?\d+", atar, re.M)
            if len(score) > 0:
                score = set(score)
                course_item["minScoreNextIntake"] = float(max(score))

        cricos = response.xpath("//*[contains(@id, 'cYear-intCricos')]").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if len(cricos) > 0:
                cricos = set(cricos)
                course_item["cricosCode"] = ", ".join(cricos)
                # course_item["internationalApplyURL"] = response.meta['url']

        int_check = response.xpath("//div[@class='nonInternational']").get()
        if int_check is None:
            course_item["internationalApps"] = 1

        availability = response.xpath("//*[text()='Session availability']/following-sibling::*").get()
        start_holder = []
        if availability is not None:
            for item in self.sessions:
                if re.search(item, availability, re.M):
                    start_holder.append(self.sessions[item])
        if len(start_holder) > 0:
            course_item["startMonths"] = "|".join(start_holder)

        duration = response.xpath("//p[contains(text(), 'Full-time:')]").get()
        if duration is not None:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))", duration)
            if len(duration_full) > 0:
                course_item["durationMinFull"] = float(duration_full[0][0])
                for period in self.teaching_periods:
                    if re.search(period, duration_full[0][1], re.I):
                        course_item["teachingPeriod"] = self.teaching_periods[period]

        course_item.set_sf_dt(self.degrees, ["/", "-"])

        yield course_item
