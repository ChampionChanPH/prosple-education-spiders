# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def master(course_item):
    if "research" in course_item["courseName"].lower():
        return "12"

    else:
        return "11"

def bachelor(course_item):
    if "honours" in course_item["sourceURL"]:
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
    blacklist_urls = [
        "https://www.usc.edu.au/learn/courses-and-programs/headstart-program-year-11-and-12-students",
        "https://www.usq.edu.au/study/short-programs",
        "https://www.usq.edu.au/study/degrees/single-courses",
        "https://www.usq.edu.au/study/degrees/english-language-programs"
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "University of Southern Queensland (USQ)"
    uidPrefix = "AU-USQ-"

    degrees = {
        "master": master,
        "bachelor": bachelor
    }

    valid_headers = {
        # 'OP/Rank': rank,
        'Study Mode': studymode,
        'Start': start,
        # 'Number of Units': units,
        'Duration': duration,
        'Campus': campus
    }

    campus_map = {
        "springfield": "788",
        "toowoomba": "787",
        "ipswich": "11715",
        "stanthorpe": "52578"
    }

    holder = []


    def parse(self, response):
        sub_categories = response.css(".degree-navigation__bottom a::attr(href)").extract()

        for sub_category in sub_categories:
            if response.urljoin(sub_category) not in self.blacklist_urls:
                yield response.follow(response.urljoin(sub_category), callback=self.category_page)

    def category_page(self, response):
        course_cards = response.css("tr.c-program-table__row")
        for row in course_cards:
            cells = row.css("td")
            course = cells[0].css("a.c-program-table__program-link::attr(href)").get()
            mode = cells[1].css("li::text").getall()
            campus = cells[2].css("li::text").getall()
            start = cells[3].css("li::text").getall()
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse, meta={"mode": mode, "campus": campus, "start": start})


    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(cleanspace(name), self.uidPrefix)

        course_item.set_sf_dt(self.degrees, ["and"])

        mode = response.meta["mode"]
        if mode:
            holder = []
            mode = " ".join(mode).lower()
            if "online" in mode or "external" in mode:
                holder.append("Online")
            if "on-campus" in mode:
                holder.append("In person")

            if holder:
                course_item["modeOfStudy"] = "|".join(holder)

        campus = response.meta["campus"]
        if campus:
            holder = []
            for item in [cleanspace(x).lower() for x in campus if x != "-"]:
                if item in list(self.campus_map.keys()):
                    holder.append(self.campus_map[item])

                else:
                    course_item.add_flag("campusNID", "Found new campus: " + item)
            if holder:
                course_item["campusNID"] = "|".join(holder)

        start = response.meta["start"]
        if start:
            months = convert_months(start)
            if months:
                course_item["startMonths"] = "|".join(months)

        overview = response.xpath("//ul[preceding-sibling::h2/text()='Overview']/li/text()").getall()
        if overview:
            overview = "\n".join(overview)
            course_item["overview"] = overview
            course_item.set_summary(overview)

        career = response.xpath("//ul[preceding-sibling::h2/text()='Career outcomes']/li/text()").getall()
        if career:
            career = "\n".join(career)
            course_item["careerPathways"] = career

        structure = response.xpath("//p[preceding-sibling::h2/text()='Degree structure']/text()").getall()
        if structure:
            course_item["courseStructure"] = "\n".join([cleanspace(x) for x in structure])

        domestic_fee = response.xpath("//td[preceding-sibling::td[contains(text(),'Domestic full fee')]]/text()").get()
        if domestic_fee:
            domestic_fee = re.findall("[\d\.]+", domestic_fee)
            if domestic_fee:
                course_item["domesticFeeAnnual"] = domestic_fee[0]
        # entry = response.xpath("//div[preceding-sibling::div//h2/text()='Entry requirements']//ul")
        # if entry:
        #     entry = entry[0].css("li::text").getall()
        #     course_item["entryRequirements"] = "\n".join(entry)
        #     for i in campus:
        #         if i not in self.holder:
        #             self.holder.append(i)
        #
        # print(self.holder)
        # summary_block = response.css("div#summary")
        # sections = summary_block.css("div.program-details__detail-section")
        # for section in sections:
        #     heading = cleanspace(section.css(".program-details__detail-heading::text").extract_first())
        #     if heading in list(self.valid_headers.keys()):
        #         value_in = section.css("ul")
        #         final_value = self.valid_headers[heading](value_in)
        #         course_item[final_value["field"]] = final_value["value"]
        #         # print(final_value)
        #         if final_value["message"] != "no error":
        #             course_item.add_flag(final_value["field"], final_value["message"])


        yield course_item
    #     dom_int = response.css(".dom-int-selector__details")
    #     if len(dom_int) == 1:
    #         international = response.request.url + "/international"
    #         yield response.follow(international, callback=self.course_parse_international, errback=self.no_international, meta={'item': course_item})
    #
    #     elif len(dom_int) == 0:
    #         yield course_item
    #
    #     # if "flag" in course_item:
    #     #     print(response.request.url)
    #     #     print(course_item["flag"])
    #
    # def no_international(self, response):
    #     course_item = response.meta["item"]
    #     yield course_item
    #
    # def course_parse_international(self, response):
    #     course_item = response.meta["item"]
    #     summary = response.css("#summary").extract_first()
    #     cricos = re.findall("CRICOS: ([\w]+)", summary)[0]
    #     fees = response.css("#fees").extract_first()
    #     fees = re.findall("AUD (\d+)", fees)
    #     total_fee = max([int(x) for x in fees])
    #     print(total_fee)
    #     print(cricos)
    #     yield course_item