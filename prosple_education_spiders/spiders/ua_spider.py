# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honour" in course_item["courseName"].lower() or "hons" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"

class UaSpiderSpider(scrapy.Spider):
    name = 'ua_spider'
    allowed_domains = ['www.auckland.ac.nz']
    start_urls = ['https://www.auckland.ac.nz/en/study/study-options/find-a-study-option.html']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "University of Auckland"
    uidPrefix = "NZ-UA-"

    degrees = {
        "master": "11",
        "bachelor": bachelor,
        "postgraduate certificate": "7",
        "postgraduate diploma": "8",
        "foundation certificate": "4"
    }

    campuses = {
        "City": "47783",
        "Epsom": "47784",
        "Grafton": "47785",
        "Newmarket": "47786",
        "Tai Tokerau": "47787",
        "Leigh Marine": "47788",
        "South Auckland": "47789"
    }
    holder = []

    def parse(self, response):
        courses = response.xpath("//ul[preceding-sibling::div/div/h3[contains(text(), 'Programmes')]]/li")
        for li in courses:
            course = li.css("a::attr(href)").get()
            name = li.css("p::attr(data-programme-name)").get()
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse, meta={"name": name})

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        # name = response.css("h1::text").get()
        name = response.meta["name"]
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees, ["and"])

        # Overide canonical group
        course_item["group"] = 2
        course_item["canonicalGroup"] = "GradNewZealand"

        overview = response.xpath("//div[preceding-sibling::div/h2/text()='Programme overview']/p/text()").getall()
        if overview:
            course_item["overview"] = cleanspace("\n".join(overview))
            course_item.set_summary(" ".join(overview))

        structure = response.xpath("//div[preceding-sibling::div/h2/text()='Programme structure']/div/div/*").getall()
        if structure:
            course_item["courseStructure"] = cleanspace("\n".join(structure))

        fees_dom = response.css(".fees-box .domestic dd::text").get()
        if fees_dom:
            fees_dom = re.findall("\$([\d,\.]+)", fees_dom)
            fees_dom = max([float(x.replace(",", "")) for x in fees_dom])
            course_item["domesticFeeAnnual"] = fees_dom

        fees_int = response.css(".fees-box .international dd::text").get()
        if fees_int:
            fees_int = re.findall("\$([\d,\.]+)", fees_int)
            course_item["internationalFeeAnnual"] = fees_int
            course_item["internationalApps"] = 1

        quick_facts = response.css("dl.quick-facts__list")
        for fact in quick_facts:
            header = cleanspace(fact.css("dt").get())
            header = re.findall("svg>\s(.*?)\s</dt>", header)[0]
            if header == "Duration":
                duration = fact.css("dd::text").getall()
                if duration:
                    for i in duration:
                        if "Full-time" in i:
                            min_full = [float(x) for x in re.findall("[\d\.]+", i)]
                            if len(min_full) > 1:
                                course_item["durationMinFull"] = min(min_full)
                                course_item["durationMaxFull"] = max(min_full)

                            elif len(min_full) == 1:
                                course_item["durationMinFull"] = min_full[0]

                            else:
                                if "half" in i:
                                    course_item["durationMinFull"] = 0.5
                                elif "Varies" not in i:
                                    course_item.add_flag("duration", "No valid Full-time duration: "+ i)

                            if "year" in i.lower():
                                course_item["teachingPeriod"] = 1

                            elif "month" in i.lower():
                                course_item["teachingPeriod"] = 12

                            else:
                                if "Varies" not in i:
                                    course_item.add_flag("teachingPeriod", "New teaching period found: "+i)

                        elif "Part-time" in  i:
                            min_part = re.findall(":\s?(\d+\s\w+)", i)
                            if min_part:
                                course_item["durationMinPart"] = min_part[0].split(" ")[0]
                            else:
                                if "Varies" not in i:
                                    course_item.add_flag("duration", "No valid Part-time duration: "+i)
                        else:
                            course_item.add_flag("duration", "New duration pattern found: "+i)

            elif header == "Next start date":
                start = fact.css("dd::text").getall()
                if start:
                    start = " ".join(start)
                    start = convert_months(start.split(" "))
                    course_item["startMonths"] = "|".join(start)

            elif header == "Available locations":
                campus = fact.css("dd::text").getall()
                campus = ", ".join(campus).split(", ")
                campus = map_convert(self.campuses, campus)
                mode = []
                if campus["converted"]:
                    mode.append("In person")
                    course_item["campusNID"] = "|".join(campus["converted"])

                for failed in campus["failed"]:
                    if failed in ["Off-campus", "Auckland Online"] and "Online" not in mode:
                        mode.append("Online")

                    elif failed not in ["", "Overseas"]:
                        course_item.add_flag("campusNID", "New campus found: "+failed)
                course_item["modeOfStudy"] = "|".join(mode)

            elif header == "Programme type":
                level = fact.css("dd::text").getall()
                if level:
                    level = " ".join(level)
                    if "Undergraduate" in level:
                        course_item["courseLevel"] = "1"
                    elif "Postgraduate" in level:
                        course_item["courseLevel"] = "2"

        # if "flag" in course_item:
        yield course_item
