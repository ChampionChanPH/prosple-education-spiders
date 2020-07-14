# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def master(course_item):
    if course_item["courseLevel"] == "research":
        return "12"

    else:
        return "11"

def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honours" in course_item["sourceURL"]:
        return "3"

    else:
        return "2"

def studymode(selector):
    holder = []
    items = selector.css("li::text").extract()
    for item in [cleanspace(x) for x in items]:
        if item == "Online":
            holder.append(item)
        else:
            holder.append("In person")

    return {"value": "|".join(list(dict.fromkeys(holder).keys())), "message": "no error", "field": "modeOfStudy"}


def rank(selector):
    pass


def start(selector):
    holder = []
    message = "no error"
    months = selector.css("li::text").extract()
    for month in months:
        # print(month)
        text = re.findall("\((.*)\)", month)[0]
        holder.append(text)

    holder = convert_months(holder)

    if len(holder) == 0:
        message = "No intake months found."

    return {"value": "|".join(list(dict.fromkeys(holder).keys())), "message": message, "field": "startMonths"}


def units(selector):
    pass


def duration(selector):
    holder = []
    message = "no error"
    items = selector.css("li::text").extract()
    full_pattern = "[\d\.]+ year/?s? or part-time equivalent"
    part_pattern = "[\d\.]+ year/?s? part-time"
    for item in [cleanspace(x) for x in items]:

        if re.search(full_pattern, item):
            value = re.findall("[\d\.]+", item)[0]
            holder.append(value)
            field = "durationMinFull"

        elif re.search(part_pattern, item):
            value = re.findall("[\d\.]+", item)[0]
            holder.append(value)
            field = "durationMinPart"

        else:
            return {"value": None, "message": "Pattern mismatch: "+item, "field": "durationRaw"}

    if len(holder) > 1 or len(holder) == 0:
        return {"value": None, "message": "No or more than 1 durations found", "field": "durationRaw"}

    return {"value": holder[0], "message": message, "field": field}


def campus(selector):
    campus_map = {
        "Springfield": "788",
        "Toowoomba": "787",
        "Ipswich": "11715",
        "-": ""
    }
    holder = []
    missing = []
    campuses = selector.css("li::text").extract()
    for campus in [cleanspace(x) for x in campuses]:
        if campus in list(campus_map.keys()):
            holder.append(campus_map[campus])
        else:
            missing.append(campus)
    if len(missing) > 0:
        message = "Following campus terms are missing: "+", ".join(missing)
    else:
        message = "no error"
    return {"value": "|".join(holder), "message": message, "field": "campusNID"}


class UsqSpiderSpider(scrapy.Spider):
    name = 'usq_spider'
    # allowed_domains = ['https://www.usq.edu.au/study']
    start_urls = ['https://www.usq.edu.au/study/']

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = ["https://www.usc.edu.au/learn/courses-and-programs/headstart-program-year-11-and-12-students"]
    scraped_urls = []
    superlist_urls = ["https://www.usq.edu.au/study/degrees/graduate-diploma-of-science/agricultural-science"]

    institution = "University of Southern Queensland (USQ)"
    uidPrefix = "AU-USQ-"

    degrees = {
        "master": master,
        "bachelor": bachelor
    }

    degree_delims = ["\s"]

    valid_headers = {
        # 'OP/Rank': rank,
        'Study Mode': studymode,
        'Start': start,
        # 'Number of Units': units,
        'Duration': duration,
        'Campus': campus
    }


    def parse(self, response):
        sub_categories = response.css(".degree-navigation__bottom a::attr(href)").extract()

        for sub_category in sub_categories:
            yield response.follow(response.urljoin(sub_category), callback=self.category_page)

    def category_page(self, response):
        categories = response.css(".button-grid a::attr(href)").extract()

        for category in categories:
            yield response.follow(response.urljoin(category), callback=self.sub_category_page)

    def sub_category_page(self, response):
        tabs = response.css("div.tab-pane")
        for tab in tabs:
            level = tab.css("div::attr(id)").extract_first()
            if level != "professional-development":
                courses = tab.css("a::attr(href)").extract()
                for course in [response.urljoin(x) for x in courses]:
                    if course not in self.blacklist_urls and course not in self.scraped_urls:
                        if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                            self.scraped_urls.append(course)
                            yield response.follow(course, callback=self.course_parse, meta={'level': level})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_item["courseName"] = response.css("h1::text").extract_first()
        if "honour" in course_item["courseName"]:
            course_item.add_flag("degreeType", course_item["courseName"] + " could be honours.")
        course_item["uid"] = self.uidPrefix + course_item["courseName"]
        course_item["courseLevel"] = response.meta["level"]  # Assigning a value to help with master (research) vs master (coursework)
        course_item.set_sf_dt(self.degrees, degree_delims=self.degree_delims)

        # info_block = response.css("div.aligned-content-top")
        # if len(info_block) > 1:
        #     info_block = response.css("div#overview div.aligned-content-top")
        #
        # # course_item["overviewSummary"] = info_block.css("h2::text").extract_first()
        # a = info_block.css("div").extract_first()
        # # print(a)
        # a = re.findall("^<div.*?>\n(.(?s)*?)</?[hd]", a)
        # a = re.sub("<.*?>","",a[0])
        # print(a)


        summary_block = response.css("div#summary")
        sections = summary_block.css("div.program-details__detail-section")
        for section in sections:
            heading = cleanspace(section.css(".program-details__detail-heading::text").extract_first())
            if heading in list(self.valid_headers.keys()):
                value_in = section.css("ul")
                final_value = self.valid_headers[heading](value_in)
                course_item[final_value["field"]] = final_value["value"]
                # print(final_value)
                if final_value["message"] != "no error":
                    course_item.add_flag(final_value["field"], final_value["message"])



        dom_int = response.css(".dom-int-selector__details")
        if len(dom_int) == 1:
            international = response.request.url + "/international"
            yield response.follow(international, callback=self.course_parse_international, errback=self.no_international, meta={'item': course_item})

        elif len(dom_int) == 0:
            yield course_item

        # if "flag" in course_item:
        #     print(response.request.url)
        #     print(course_item["flag"])

    def no_international(self, response):
        course_item = response.meta["item"]
        yield course_item

    def course_parse_international(self, response):
        course_item = response.meta["item"]
        summary = response.css("#summary").extract_first()
        cricos = re.findall("CRICOS: ([\w]+)", summary)[0]
        fees = response.css("#fees").extract_first()
        fees = re.findall("AUD (\d+)", fees)
        total_fee = max([int(x) for x in fees])
        print(total_fee)
        print(cricos)
        yield course_item