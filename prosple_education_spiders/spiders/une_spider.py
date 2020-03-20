import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class UneSpiderSpider(scrapy.Spider):
    name = 'une_spider'
    allowed_domains = ['my.une.edu.au', 'une.edu.au']
    start_urls = ['http://my.une.edu.au/courses/2020/courses/browse/']
    campuses = {"Sydney": "765", "Armidale": "764"}
    degrees = {"Graduate Certificate": "Graduate Certificate",
               "Graduate Diploma": "Graduate Diploma",
               "Honours": "Bachelor (Honours)",
               "Research": "Masters (Research)",
               "Master": "Masters (Coursework)",
               "Doctor": "Doctorate (PhD)",
               "Bachelor": "Bachelor",
               "Certificate": "Certificate",
               "Diploma": "Diploma"}
    group = [["Postgraduate", 4, "PostgradAustralia"], ["Undergraduate", 3, "The Uni Guide"]]

    def parse(self, response):
        courses = response.xpath("//div[@class='content']//td/a/@href").getall()
        courses= ["https://my.une.edu.au/courses/2020/courses/BAGLAW"]

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of New England (UNE)"
        uidPrefix = "AU-UNE-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution

        course_item["courseName"] = response.xpath("//div[@class='main-content']//h2/text()").get()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])
        for degree in self.degrees:
            if re.search(degree, course_item["courseName"], re.IGNORECASE):
                course_item["degreeType"] = self.degrees[degree]
                break
            else:
                course_item["degreeType"] = ""
        if course_item["degreeType"] == "":
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
        if re.search("/", course_item["courseName"]):
            course_item["doubleDegree"] = 1
        separate_holder = course_item["courseName"].split("/")
        holder = []
        for item in separate_holder:
            if re.search("\s(in|of)\s", item):
                holder.append(re.findall("(?<=[in|of]\s)(.+)", item, re.DOTALL)[0])
            else:
                holder.append(item)
        course_item["specificStudyField"] = "/".join(holder)
        lower_holder = []
        for item in holder:
            lower_holder.append(item.lower())
        course_item["rawStudyfield"] = lower_holder[:]

        course_item["teachingPeriod"] = 1

        overview = response.xpath("//div[@id='overviewTab']/div[@id='overviewTab-leftColumn']").get()
        course_item["overview"] = strip_tags(overview, False)

        course_item["domesticApplyURL"] = response.request.url
        course_item["internationalApplyURL"] = response.request.url

        table_holder = []
        for title, description in zip(response.xpath("//table[@id='furtherInformationTable']/tr/td[1]").getall(),
                                      response.xpath("//table[@id='furtherInformationTable']/tr/td[2]").getall()):
            title = re.sub("</?td>", "", title)
            description = re.sub("</?td>", "", description)
            holder = [title.strip(), description.strip()]
            table_holder.append(holder)

        for row in table_holder:
            if re.search("abbreviation", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["courseCode"] = row[1]
            if re.search("cricos", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["cricosCode"] = row[1]
                course_item["internationalApps"] = 1
            if re.search("commencing", row[0], re.IGNORECASE | re.MULTILINE):
                study_holder = []
                campus_holder = []
                if re.search("campus", row[1], re.IGNORECASE | re.MULTILINE):
                    study_holder.append("In Person")
                if re.search("online", row[1], re.IGNORECASE | re.MULTILINE):
                    study_holder.append("Online")
                course_item["modeOfStudy"] = "|".join(study_holder)
                for campus in self.campuses:
                    if re.search(campus, row[1], re.IGNORECASE | re.MULTILINE):
                        campus_holder.append(self.campuses[campus])
                course_item["campusNID"] = "|".join(campus_holder)
            if re.search("duration", row[0], re.IGNORECASE | re.MULTILINE):
                full_time = re.findall("[0-9]*?\.*?[0-9]+?(?=\s[Yyears]+?\s[Ff]ull.time)", row[1],
                                       re.DOTALL | re.MULTILINE)
                part_time = re.findall("[0-9]*?\.*?[0-9]+?(?=\s[Yyears]+?\s[Pp]art.time)", row[1],
                                       re.DOTALL | re.MULTILINE)
                if len(full_time) > 0:
                    course_item["durationMinFull"] = float(full_time[0])
                if len(part_time) > 0:
                    course_item["durationMinPart"] = float(part_time[0])
                if len(part_time) == 0 and len(full_time) > 0:
                    course_item["durationMinPart"] = float(full_time[0]) * 2
            if re.search("Guaranteed ATAR", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["guaranteedEntryScore"] = row[1]
            if re.search("Entry Requirements", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["entryRequirements"] = strip_tags(row[1], False)
            if re.search("How to Apply", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["howToApply"] = strip_tags(row[1], False)

        table_holder = []
        for title, description in zip(response.xpath("//table[@id='courseOutcomesTable']/tr/td[1]").getall(),
                                      response.xpath("//table[@id='courseOutcomesTable']/tr/td[2]").getall()):
            title = re.sub("</?td>", "", title)
            description = re.sub("</?td>", "", description)
            holder = [title.strip(), description.strip()]
            table_holder.append(holder)

        for row in table_holder:
            if re.search("Course Aims", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["overviewSummary"] = strip_tags(row[1])
            if re.search("learning", row[0], re.IGNORECASE | re.MULTILINE):
                course_item["whatLearn"] = strip_tags(row[1], False)

        yield course_item