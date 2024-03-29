# -*- coding: utf-8 -*-
# by: Johnel Bacani
# Updated by: Christian Anasco - added set_summary on overviewSummary and added strip_tags on some html fields

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


class UnsSpiderSpider(scrapy.Spider):
    name = 'uns_spider'
    # allowed_domains = ['https://degrees.unsw.edu.au/']
    start_urls = ['https://degrees.unsw.edu.au/']
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "University of New South Wales (UNSW)"
    uidPrefix = "AU-UNS-"

    degrees = {
        "postgraduate certificate": "7",
        "graduate certificate": "7",
        "agsm graduate certificate": "7",
        "postgraduate diploma": "8",
        'science graduate diploma': '8',
        "graduate diploma": "8",
        "senior executive master": research_coursework,
        "executive master": research_coursework,
        "agsm master": research_coursework,
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctoral program": "6",
        "doctor": "6",
        "specialist certificate": "4",
        "professional certificate": "14",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "juris doctor": "10",
        "non-award": "13",
        "no match": "15"
    }

    campus = {
        "Kensington": "766",
        "Kensignton": "766",
        "UNSW Canberra": "771",
        "Paddington": "768",
        "Kensington and Rural Clinical Schools": "766",
        "Shanghai": "43320"
    }

    terms = {
        "1": "Feb",
        "2": "May",
        "3": "Sep",
        "4": "Jan"
    }

    holder = []
    def parse(self, response):
        paths = response.css("script#webpack-manifest::text").extract_first()
        paths = re.findall("path---(.*?)\.js", paths)
        paths = [re.sub("-\w+$","",x) for x in paths]
        courses = ["https://degrees.unsw.edu.au/" + x + "/?studentType=domestic" for x in paths if x not in ['404', 'compare', 'index', '404-html', '']]

        for course in courses:
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        # course_item["domesticApplyURL"] = response.request.url

        course_name = response.css("h1.banner__title::text").extract_first()
        award = response.xpath("//dd[preceding-sibling::dt/text()='Award']/div/p/text()").get()
        if award:
            course_item["courseName"] = award if "/" in course_name else course_name
        else:
            course_item["courseName"] = course_name

        # Override for Juris Doctor
        if course_item["courseName"] == "Juris Doctor":
            course_item["courseName"] = "Juris Doctor in Law"

        # Override weird course with 4 degrees
        if course_name == "Bachelor of Engineering (Materials Science) (Honours)/Master of Biomedical Engineering":
            course_item["courseName"] = "Bachelor of Engineering (Materials Science) (Honours)/Master of Biomedical Engineering"

        # Override Bachelor of Bachelor of Arts
        if "Bachelor of Bachelor of" in course_item["courseName"]:
            course_item["courseName"] = re.sub("Bachelor of Bachelor of", "Bachelor of", course_item["courseName"])
        # course_item["courseName"] = award if "," in award else course_name

        course_item.set_sf_dt(self.degrees, degree_delims=['/', ','], type_delims=['of', 'in', 'by'])

        course_item.set_course_name(course_name, self.uidPrefix)

        delivery = response.xpath("//dd[preceding-sibling::dt/text()='Delivery Mode']/div/p/text()").get()

        if delivery:
            course_item["modeOfStudy"] = []
            if "face" in delivery.lower():
                course_item["modeOfStudy"].append("In person")
            if "campus" in delivery.lower():
                course_item["modeOfStudy"].append("In person")
            if "online" in delivery.lower():
                course_item["modeOfStudy"].append("Online")

            course_item["modeOfStudy"] = "|".join(list(set(course_item["modeOfStudy"])))

        code = response.xpath("//dd[preceding-sibling::dt/text()='Program Code']/div/p/text()").get()
        if code:
            course_item["courseCode"] = code
            course_item['uid'] = course_item['uid'] + '-' + code

        cricos = response.xpath("//dd[preceding-sibling::dt/text()='CRICOS Code']/div/p/text()").get()
        if cricos and cricos != "N/A^":
            course_item["cricosCode"] = cricos

        campuses = response.xpath("//dd[preceding-sibling::dt/text()='Campus']/div/p/text()").get()
        if campuses:
            campuses = campuses.split(" & ")
            campuses = map_convert(self.campus, campuses)
            course_item["campusNID"] = "|".join(campuses["converted"])
            if campuses["failed"]:
                course_item.add_flag("campusNID", "The following campuses were not mapped: "+", ".join(campuses["failed"]))

        duration = response.xpath("//dd[preceding-sibling::dt/text()='Duration']/div/p/text()").get()
        course_item["teachingPeriod"] = 1
        if duration:
            pattern_full = "([\d\.]+)\+?\syears?\sfull[-\s]time"
            pattern_full2 = "([\d\.]+)\+?\syears?$"
            pattern_part = "([\d\.]+)\+?\syears?\spart[-\s]time"
            part_time = re.findall(pattern_part, duration)
            full_time = re.findall(pattern_full, duration)
            full_time2 = re.findall(pattern_full2, duration)
            if part_time:
                course_item["durationMinPart"] = part_time[0]

            if full_time:
                course_item["durationMinFull"] = full_time[0]
            elif full_time2:
                course_item["durationMinFull"] = full_time2[0]

            if "durationMinPart" not in course_item and "durationMinFull" not in course_item:
                course_item.add_flag("durations", "No durations were found")

        #     duration = re.sub("[\.\d]+\+?\s", "", duration)
        # if duration not in self.holder:
        #     self.holder.append(duration)

        overview = response.xpath("//div[preceding-sibling::h1/text()='Overview']/div/p").getall()
        if overview:
            summary = [strip_tags(x) for x in overview if strip_tags(x) != '']
            course_item.set_summary(' '.join(summary))
            course_item["overview"] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        dom_fee = response.xpath("//dd[preceding-sibling::dt/text()='2020 Indicative First Year Fee']/div/p/text()").get()
        if dom_fee and dom_fee != "$TBC":
            holder = re.findall("\$(\d*),?(\d+)", dom_fee)
            if not holder:
                holder = re.findall("(\d*),?(\d+)", dom_fee)
            if holder:
                course_item["domesticFeeAnnual"] = holder[0][0] + holder[0][1]
        else:
            print("No Dom Fee")

        # entry = response.css("section#entry-requirements div.text").extract_first()
        # if entry:
        #     course_item["entryRequirements"] = entry

        apply = response.css("section#how-to-apply div.text").extract_first()
        if apply:
            course_item["howToApply"] = strip_tags(apply, remove_all_tags=False, remove_hyperlinks=True)

        intakes = response.xpath("//dd[preceding-sibling::dt/text()='Commencing Terms']/div/p/text()").get()
        if intakes:
            intakes = re.sub("Summer", "4", intakes)
            intakes = re.findall("\s(\d)\*?\s", intakes)
            intakes = map_convert(self.terms, intakes)
            intakes = convert_months(intakes["converted"])
            if intakes:
                course_item["startMonths"] = "|".join(intakes)

        student_type = response.css(".banner__student-type-msg::text").extract_first()
        if student_type != "Only for domestic students":
            course_item["internationalApps"] = 1
            # course_item["internationalApplyURL"] = re.sub("domestic$", "international", response.request.url)

        min_atar = response.xpath("//dd[preceding-sibling::*/text()= '2021 Guaranteed Entry']/div/p/text()").get()
        if min_atar:
            try:
                min_atar = float(min_atar)
                course_item["lowestScore"] = min_atar
            except:
                pass

        #international
        # international = re.sub("domestic$","international", response.request.url)
        # yield SplashRequest(international, callback=self.int_course_parse, args={'wait': 10}, meta={'url': international, "item": course_item})
        # yield response.follow(international, callback=self.int_course_parse, meta={"item": course_item})


        # print(self.holder)
        # if "flag" in course_item:
        #     yield course_item

        yield course_item

    # def int_course_parse(self, response):
    #     course_item = response.meta["item"]
    #     course_item["internationalApplyURL"] = response.meta["url"]
    #     # int_fee = response.xpath("//dd[preceding-sibling::dt/text()='2020 Indicative First Year Fee']/div/p/text()").get()
    #     int_fee = response.css("body").extract_first()
    #     print(int_fee)
        # if int_fee and int_fee != "$TBC":
        #     int_fee = re.findall("\$([\d\.\,]+)", int_fee)
        #     course_item["internationalFeeAnnual"] = re.sub(",", "", int_fee[0])
        #
        # else:
        #     print("No Int Fee")

        # yield course_item