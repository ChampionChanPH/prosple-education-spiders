import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class UotSpiderSpider(scrapy.Spider):
    name = 'uot_spider'
    allowed_domains = ['www.utas.edu.au', 'utas.edu.au']
    start_urls = ['https://www.utas.edu.au/courses/undergraduate',
                  'https://www.utas.edu.au/courses/postgraduate']
    campuses = {"Rozelle": "815",
                "Launceston": "810",
                "Distance Launceston": "813",
                "Darlinghurst": "816",
                "Distance Sydney": "817",
                "Distance Hobart": "814",
                "Hobart": "811",
                "Cradle Coast": "812"}
    terms = {"Term 1": "02",
             "Term 2": "04",
             "Term 3": "07",
             "Term 4": "10",
             "Semester 1": "02",
             "Semester 2": "07"}
    degrees = {"Graduate Certificate": "Graduate Certificate",
               "Graduate Diploma": "Graduate Diploma",
               "with Honours": "Bachelor (Honours)",
               "Research": "Masters (Research)",
               "Master": "Masters (Coursework)",
               "Doctor": "Doctorate (PhD)",
               "Bachelor": "Bachelor",
               "Associate Degree": "Associate Degree",
               "Certificate": "Certificate",
               "Diploma": "Diploma"}
    group = [["Postgraduate", 4, "PostgradAustralia"], ["Undergraduate", 3, "The Uni Guide"]]

    def parse(self, response):
        courses = response.xpath("//div[@id='courseList']//div[@class='content-border']//a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of Tasmania"
        uidPrefix = "AU-UOT-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution

        course_item["courseName"] = response.xpath("//h1[@class='l-object-page-header--page-title']/text()").get()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])
        for degree in self.degrees:
            if "degreeType" in course_item:
                break
            if re.search(degree, course_item["courseName"], re.IGNORECASE):
                course_item["degreeType"] = self.degrees[degree]
        if "degreeType" not in course_item:
            course_item["degreeType"] = "Non-Award"
        if course_item["degreeType"] in ["Graduate Certificate", "Graduate Diploma", "Bachelor (Honours)",
                                         "Masters (Research)", "Masters (Coursework)", "Doctorate (PhD)"]:
            course_item["courseLevel"] = self.group[0][0]
            course_item["group"] = self.group[0][1]
            course_item["canonicalGroup"] = self.group[0][2]
        elif course_item["degreeType"] in ["Bachelor", "Certificate", "Diploma"]:
            course_item["courseLevel"] = self.group[1][0]
            course_item["group"] = self.group[1][1]
            course_item["canonicalGroup"] = self.group[1][2]
        else:
            course_item["courseLevel"] = ""
            course_item["group"] = self.group[1][1]
            course_item["canonicalGroup"] = self.group[1][2]

        separate_holder = re.split(" and (?=Bachelor|Graduate|Diploma|Master|Doctor)", course_item["courseName"])
        if len(separate_holder) > 1:
            course_item["doubleDegree"] = 1
        holder = []
        for item in separate_holder:
            if re.search("\s(in|of)\s", item):
                item = re.sub(" with Honours", "", item, 0, re.IGNORECASE)
                holder.append(re.findall("(?<=[in|of]\s)(.+)", item, re.DOTALL)[0])
            else:
                holder.append(item)
        course_item["specificStudyField"] = "/".join(holder)
        lower_holder = []
        for item in holder:
            lower_holder.append(item.lower())
        course_item["rawStudyfield"] = lower_holder[:]

        course_code = response.xpath("//h1[@class='l-object-page-header--page-title']/small/text()").get()
        course_code = re.findall("(?<=\()(.+?)(?=\))", course_code, re.DOTALL)
        if len(course_code) > 0:
            course_item["courseCode"] = course_code[0]

        course_details = response.xpath("//div[contains(@class, 'tabbed-content')]").getall()
        course_details = "".join(course_details)
        campus_holder = []
        term_holder = set()
        if len(course_details) > 0:
            cricos_code = re.findall("[0-9]{6}[0-9a-zA-Z]{1}", course_details, re.MULTILINE)
            min_full = re.findall(r"minimum ([0-9]?\.?[0-9]+?) year", course_details, re.MULTILINE | re.IGNORECASE)
            max_part = re.findall(r"maximum of ([0-9]?\.?[0-9]+?) year", course_details, re.MULTILINE | re.IGNORECASE)
            for campus in self.campuses:
                if campus in ["Launceston", "Hobart"]:
                    if re.search(r"[^(Distance )]" + campus, course_details, re.MULTILINE | re.IGNORECASE):
                        campus_holder.append(self.campuses[campus])
                else:
                    if re.search(campus, course_details, re.MULTILINE | re.IGNORECASE):
                        campus_holder.append(self.campuses[campus])
            for term in self.terms:
                if re.search(term, course_details, re.MULTILINE | re.IGNORECASE):
                    term_holder.add(self.terms[term])
        if len(cricos_code) > 0:
            course_item["cricosCode"] = cricos_code[0]
            course_item["internationalApps"] = 1
        if len(min_full) > 0:
            course_item["durationMinFull"] = float(min_full[0])
        if len(max_part) > 0:
            course_item["durationMaxPart"] = float(max_part[0])
        if len(max_part) == 0 and len(min_full) > 0:
            course_item["durationMaxPart"] = float(min_full[0]) * 2
        course_item["teachingPeriod"] = 1
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(campus_holder)
        if "campusNID" in course_item:
            if re.search("813|814|817", course_item["campusNID"]) and re.search("810|811|812|815|816",
                                                                                course_item["campusNID"]):
                course_item["modeOfStudy"] = "In Person|Online"
            elif re.search("810|811|812|815|816", course_item["campusNID"]):
                course_item["modeOfStudy"] = "In Person"
            elif re.search("813|814|817", course_item["campusNID"]):
                course_item["modeOfStudy"] = "Online"
        if len(term_holder) > 0:
            course_item["startMonths"] = "|".join(term_holder)

        course_item["domesticApplyURL"] = response.request.url
        course_item["internationalApplyURL"] = response.request.url

        course_item["overviewSummary"] = response.xpath("//div[@class='richtext richtext__medium']/div["
                                                        "@class='lede']/text()").get()
        overview = response.xpath(
            "//div[@class='block block__gutter-md block__shadowed']/div[@class='block block__pad-lg']/div["
            "@class='richtext richtext__medium']/*[not(contains(@class, 'lede'))]").getall()
        if len(overview) > 0:
            course_item["overview"] = strip_tags("".join(overview), False)

        entry = response.xpath("//div[@id='c-entry-eligibility']").get()
        if entry is not None:
            course_item["entryRequirements"] = strip_tags(entry, False)

        other_details = response.xpath("//div[@class='block block__pad-lg block__shadowed']").getall()
        other_details = "".join(other_details)
        annual_fee = re.findall(r"rate of \$([0-9]*?),?([0-9]{3}) AUD per standard", other_details, re.MULTILINE)
        if len(annual_fee) > 0:
            course_item["internationalFeeAnnual"] = float("".join(annual_fee[0]))
        annual_fee = re.findall(r"2020 Annual Tuition Fee \(international students\): <strong>\$([0-9]*?),?([0-9]{3})",
                                other_details, re.MULTILINE)
        if len(annual_fee) > 0:
            course_item["internationalFeeAnnual"] = float("".join(annual_fee[0]))

        if "internationalFeeAnnual" in course_item and "durationMinFull" in course_item:
            course_item["internationalFeeTotal"] = course_item["internationalFeeAnnual"] * course_item["durationMinFull"]

        yield course_item
