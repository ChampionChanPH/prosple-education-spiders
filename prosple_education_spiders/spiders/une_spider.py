import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


class UneSpiderSpider(scrapy.Spider):
    name = 'une_spider'
    allowed_domains = ['my.une.edu.au', 'une.edu.au']
    start_urls = ['http://my.une.edu.au/courses/2020/courses/browse/']
    banned_urls = ['https://my.une.edu.au/courses/2020/courses/GDPSYA',
                   'https://my.une.edu.au/courses/2020/courses/MHMI']
    institution = "University of New England (UNE)"
    uidPrefix = "AU-UNE-"
    campuses = {"Sydney": "765", "Armidale": "764"}
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
        courses = response.xpath("//div[@class='content']//td/a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath("//h2/text()").get()
        if course_name is not None:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

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
            if re.search(r"Guaranteed ATAR", row[0], re.I | re.M):
                course_item["guaranteedEntryScore"] = row[1]
            if re.search(r"Entry Requirements", row[0], re.I | re.M):
                course_item["entryRequirements"] = strip_tags(row[1], False)
            if re.search(r"How to Apply", row[0], re.I | re.M):
                course_item["howToApply"] = strip_tags(row[1], False)

        table_holder = []
        for title, description in zip(response.xpath("//table[@id='courseOutcomesTable']/tr/td[1]").getall(),
                                      response.xpath("//table[@id='courseOutcomesTable']/tr/td[2]").getall()):
            title = re.sub("</?td>", "", title)
            description = re.sub("</?td>", "", description)
            holder = [title.strip(), description.strip()]
            table_holder.append(holder)

        for row in table_holder:
            if re.search(r"Course Aims", row[0], re.I | re.M):
                course_item["overviewSummary"] = strip_tags(row[1])
            if re.search("learning", row[0], re.I | re.M):
                course_item["whatLearn"] = strip_tags(row[1], False)

        course_item.set_sf_dt(self.degrees)

        if not re.search(r"This course is not offered in 2020", course_item["overview"], re.M | re.I) or \
                not re.search(r"Exit Award only", course_item["overview"], re.M | re.I) or \
                not re.search(r"Applications for 2020 Open Soon", course_item["overview"], re.M | re.I) or \
                response.request.url not in self.banned_urls:
            yield course_item
