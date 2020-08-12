# -*- coding: utf-8 -*-

from ..standard_libs import *

def bachelor(course_item):
    if "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class TiwaSpiderSpider(scrapy.Spider):
    name = 'tiwa_spider'
    # allowed_domains = ['https://www.tafeinternational.wa.edu.au/your-study-options/study-at-tafe/course-catalogue']
    start_urls = [
        'https://www.tafeinternational.wa.edu.au/your-study-options/study-at-tafe/course-catalogue/'
    ]

    campus_map = {
        "Albany": "38027",
        "Balga": "38029",
        "Bentley": "38030",
        "Bunbury": "38031",
        "Carlisle": "38032",
        "East Perth": "38033",
        "Fremantle": "38034",
        "Geraldton": "38035",
        "Jandakot": "38036",
        "Joondalup (Kendrew Crescent)": "38038",
        "Kwinana": "38039",
        "Leederville": "38040",
        "Margaret River": "38041",
        "Mt Lawley": "38042",
        "Munster": "38043",
        "Murdoch": "38044",
        "Perth": "38045",
        "Rockingham": "38046",
        "Thornlie": "38047"
    }

    course_data_map = {
        "Duration:": "durationMinFull",
        "Tuition fee:": "feesRaw",
        "Resource fee:": "feesRaw",
        "Materials fee:": "feesRaw"

    }

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'

    institution = "TAFE International Western Australia"
    uidPrefix = "AU-TIWA-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
    }

    def parse(self, response):
        categories = response.css("div#MSOZoneCell_WebPartWPQ4 a::attr(href)").extract()
        # print(len(courses))
        for category in categories:
            # print(category)
            yield response.follow(category, callback=self.courses)
            # yield SplashRequest(response.urljoin(category), callback=self.course_parse)

    def courses(self, response):
        courses = response.css("a.view-course-btn::attr(href)").extract()
        # print(len(courses))
        for course in courses:
            yield SplashRequest(response.urljoin(course), callback=self.course_parse, args={'wait': 5}, meta={'url': response.urljoin(course)})

    def course_parse(self, response):
        canonical_group = "StudyPerth"
        group_number = 23


        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta['url']
        course_item["group"] = group_number
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["canonicalGroup"] = canonical_group
        course_item["internationalApplyURL"] = response.meta['url']
        course_item["domesticApplyURL"] = response.meta['url']

        raw_course_name = response.css("#main h1::text").extract_first()
        if raw_course_name:
            if raw_course_name == "Advanced Diploma of Maritime Operations - Master Unlimited":
                course_item.set_course_name("Advanced Diploma of Maritime Operations", self.uidPrefix)
                course_item.set_sf_dt(self.degrees)
                course_item.set_course_name("Advanced Diploma of Maritime Operations - Master Unlimited", self.uidPrefix)

            else:
                if len(re.findall("\d",raw_course_name.split(" ")[0])) > 0:
                    course_item.set_course_name(re.sub(raw_course_name.split(" ")[0]+" ","",raw_course_name), self.uidPrefix)
                    # course_item["courseCode"] = raw_course_name.split(" ")[0]

                else:
                    course_item.set_course_name(raw_course_name, self.uidPrefix)
                course_item.set_sf_dt(self.degrees)
        else:
            return

        course_item["uid"] = self.uidPrefix + course_item["courseName"]

        # StudyPerth override
        course_item["group"] = 23
        course_item["canonicalGroup"] = "StudyPerth"

        codes = response.css("hgroup h3::text").extract_first()
        # print(codes)
        if codes:
            try:
                course_item["courseCode"] = re.findall("National code: (.*?)\s",codes)[0]
                course_item["cricosCode"] = re.findall("CRICOS code: ([\w\d]*)",codes)[0]

            except IndexError:
                print("Missing code")

        overview = response.css("article.first p::text").extract()
        if overview:
            course_item["overviewSummary"] = overview[0]
            course_item["overview"] = "\n".join(overview)

        entry = response.css("ul#admission-req").extract_first()
        if entry:
            course_item["entryRequirements"] = entry

        pathways = response.css('div#ctl00_PlaceHolderMain_ctl00_CourseOutline_CourseCareerOpportunities_CareerOpportunities ul').extract_first()
        if pathways:
            course_item["careerPathways"] = pathways

        campuses = unique_list(response.css('span[data-bind*="text: Campus.Location()"]::text').extract())
        if campuses:
            campuses = map_convert(self.campus_map, campuses)
            course_item["campusNID"] = "|".join(campuses["converted"])


        course_data = response.css("table.course-data tr")
        course_item["feesRaw"] = []
        for row in course_data:
            row_td = row.css("td").extract_first()
            row_span = row.css("th span::text").extract_first()
            if row_td and row_span:
                if row_span == "Duration:":
                    duration_raw = re.findall("-->(.*?)<!",row_td)[0].split(" ")
                    course_item["durationMinFull"] = float(duration_raw[0])
                    course_item["teachingPeriod"] = get_period(duration_raw[1])

                    intakes = cleanspace(row.css("#SelectedIntakes::text").extract_first())
                    intakes = intakes.strip("()").split(" ")
                    intakes = convert_months(intakes)
                    course_item["startMonths"] = "|".join(intakes)

                elif "tuition fee" in row_span.lower():
                    value = re.sub(",","",re.findall("\$([\d,]+)",row_td)[0])
                    period = re.findall("per\s(\w+)",row_td)
                    multiplier = re.findall("\((\d+)\s\w+\)",row_td)

                    if period:
                        multiplier = int(multiplier[0])
                        if period[0] == "semester" and multiplier > 1:
                            course_item["internationalFeeAnnual"] = int(value) * 2
                        course_item["internationalFeeTotal"] = int(value) * multiplier


        # if "flag" in course_item:
        yield course_item

