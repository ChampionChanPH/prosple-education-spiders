# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import Course
from ..misc_functions import *
from datetime import date
from scrapy_splash import SplashRequest



def get_duration(str_in):
    '''
    :param str_in: number followed by period. ex. 20 weeks
    :return: (duration, teaching period)
    '''

    periods = {"year": 1, "semester": 2, "trimester": 3, "quarter": 4, "month": 12, "week": 52, "day": 365}

    str_in = str_in.split(" ")
    duration = str_in[0]
    if len(str_in) == 2:
        if str_in[1][-1] == "s":
            str_in[1] = str_in[1][:-1]

        if str_in[1] in list(periods.keys()):
            period = periods[str_in[1]]
            return [duration, period]

        else:
            return [0, 1]

    else:
        return [0, 1]





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

    degrees = {"graduate certificate": {"level": "Postgraduate", "type": "Graduate Certificate"},
               "graduate diploma": {"level": "Postgraduate", "type": "Graduate Diploma"},
               "honours": {"level": "Undergraduate", "type": "Bachelor (Honours)"},
               "bachelor": {"level": "Undergraduate", "type": "Bachelor"},
               "certificate": {"level": "Undergraduate", "type": "Certificate"},
               "diploma": {"level": "Undergraduate", "type": "Diploma"},
               "non-award": {"level": "Undergraduate", "type": "Non-Award"}
               }

    def parse(self, response):
        courses = response.css(".details-btn a::attr(href)").extract()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)
            # yield SplashRequest(response.follow(course, callback=self.course_parse))
            # yield SplashRequest(response.urljoin(course), callback=self.course_parse)
    def course_parse(self, response):
        canonical_group = "StudyPerth"
        group_number = 23
        institution = "Stanley College"
        uidPrefix = "AU-SNC-"

        # print("Hey")

        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["group"] = group_number
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["canonicalGroup"] = canonical_group

        raw_course_name = cleanspace(''.join([i if ord(i) < 128 else ' ' for i in response.css("h1::text").extract_first()]))

        if len(re.findall("\d",raw_course_name.split(" ")[0])) > 0:
            course_item["courseName"] = re.sub(raw_course_name.split(" ")[0]+" ","",raw_course_name)
            course_item["courseCode"] = raw_course_name.split(" ")[0]

        else:
            course_item["courseName"] = raw_course_name

        course_item.set_raw_sf()

        # print(course_item["rawStudyfield"])
        degree_match = max([x for x in list(dict.fromkeys(self.degrees)) if x in course_item["degreeType"][0]], key=len) #match degree type and get longest match
        course_item["degreeType"] = self.degrees[degree_match]["type"]
        course_item["courseLevel"] = self.degrees[degree_match]["level"]

        course_item["uid"] = uidPrefix + course_item["courseName"]
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        cricos = response.css("div.section-head span::text").extract()
        if len(cricos) > 0:
            course_item["cricosCode"] = cricos[0].split(" ")[-1]
            course_item["internationalApps"] = 1

        overview = response.css("div.course-inside p::text").extract()
        if len(overview) > 0:

            course_item["overview"] = cleanspace("\n".join([x.strip("\n") for x in overview]))

            if len(course_item["overview"].split(".")) > 2:
                course_item["overviewSummary"] = ".".join(course_item["overview"].split(".")[:2])+"."

            else:
                course_item["overviewSummary"] = course_item["overview"]

        info = response.css("div.course-tab-content")
        contents = info.extract()
        for i in range(len(info)):
            heading = info[i].css("h2::text").extract_first()
            if heading in self.content_map.keys():
                # print("Heading:", heading)
                content = contents[i]
                content = re.sub("^.(?s)*?</h2>", "", content)#remove div and h2 part
                content = re.sub("</div>.(?s)*?$", "", content)#remove end part
                content = content.strip(" \n\r")
                course_item[self.content_map[heading]] = content

        #clean intake months
        if "startMonths" in course_item:
            month_candidates = re.findall("\w+",course_item["startMonths"])
            final_months = []
            for month in month_candidates:
                holder = get_month(month)
                if holder != "":
                    final_months.append(str(holder).zfill(2))
            course_item["startMonths"] = "|".join(list(dict.fromkeys(final_months))) #dict from keys is a trick to remove duplicate values.
            # print(course_item["startMonths"])

        #clean duration
        if "durationMinFull" in course_item:
            current = [1, 100000]#initial value that is sure to be lower than any new value
            for duration in re.findall("\d+\s\w+", course_item["durationMinFull"]):
                holder = get_duration(duration)
                if float(holder[0])/float(holder[1]) > current[0]/current[1]:
                    current = [float(x) for x in holder]

            if current != [1, 100000]:
                course_item["durationMinFull"] = int(current[0])
                course_item["teachingPeriod"] = int(current[1])

            else:
                course_item["durationMinFull"] = ""
            # print(re.findall("\d+\s\w+", course_item["durationMinFull"]))
            # print(current)

        # clean study mode
        if "modeOfStudy" in course_item:
            # print(course_item["modeOfStudy"])
            if re.findall("Face-to-face", course_item["modeOfStudy"], re.IGNORECASE):
                course_item["modeOfStudy"] = "In person"

        #clean domestic Fee Annual
        if "domesticFeeTotal" in course_item:
            # print(course_item["domesticFeeTotal"])
            tuitions = re.findall("\$([\d,]*)", course_item["domesticFeeTotal"])
            # print(tuitions)

            tuitions = [int(re.sub(",","",x)) for x in tuitions]

            course_item["domesticFeeTotal"] = max(tuitions)
            # print(course_item["domesticFeeTotal"])

            # print(len(tuitions))
            # print(tuitions)

        yield course_item

