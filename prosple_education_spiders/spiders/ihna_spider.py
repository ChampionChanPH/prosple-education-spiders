import scrapy
import re
from ..items import Course
from datetime import date

def cleanspace(str_in):
    return re.sub(r'\s+', ' ', str_in).strip(' ')


class IHNASpider(scrapy.Spider):
    name = 'ihna_spider'
    start_urls = [
        "https://ihna.edu.au/courses/"
    ]

    periods = {"Year": 1, "Semester": 2, "Trimester": 3, "Quarter": 4, "Month": 12, "Week": 52, "Day": 365}

    campus_map = {
        "Sydney Campus": "37787",
        "Perth Campus": "37788",
        "Melbourne (Heidelberg) Campus": "37789",
        "Melbourne (CBD) Campus": "37790",
        "North Melbourne Campus": "37791",
        "Melbourne CBD Campus": "37790"
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
        courses = response.css("div.col-lg-12").css("a.text-decoration-none::attr(href)").extract()
        self.international = [i for i in courses if bool(re.search("int$",i))]
        domestic = [i for i in courses if not(bool(re.search("int$",i)))]

        for course in domestic:
            yield response.follow(course, callback=self.course_parse)


    def course_parse(self, response):
        # print("test")
        canonical_group = "StudyPerth"
        group_number = 23
        institution = "Institute of Health and Nursing Australia"
        uidPrefix = "AU-IHNA-"

        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["group"] = group_number
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["canonicalGroup"] = canonical_group


        # print(response.css("#inner-header strong::text").extract_first())
        full_course_name = re.sub("(\s\W\s)", "-", response.css("#inner-header strong::text").extract_first())
        # print(full_course_name)
        if "-" in full_course_name:
            course_item["courseName"] = full_course_name.split("-")[-1]
            course_item["courseCode"] = full_course_name.split("-")[0]

        else:
            course_item["courseCode"] = full_course_name.split(" ")[0]
            course_item["courseName"] = full_course_name[len(course_item["courseCode"]):].strip(" ")

        course_item.set_raw_sf()

        degree_match = max([x for x in list(dict.fromkeys(self.degrees)) if x in course_item["degreeType"]], key=len)  # match degree type and get longest match
        course_item["degreeType"] = self.degrees[degree_match]["type"]
        course_item["courseLevel"] = self.degrees[degree_match]["level"]

        course_item["uid"] = uidPrefix + course_item["courseName"]
        course_item["overview"] = response.css("p.text-justify::text").extract()
        course_item["overviewSummary"] = course_item["overview"][0]
        course_item["overview"] = "\n".join(course_item["overview"])
        course_item["courseLevel"] = "Undergraduate"
        course_item["studyField"] = "Medical & Health Sciences"

        # course_item["campusNID"] = response.css("div.campus").css("a::text").extract()
        campus = response.css("div.campus").css("a::text").extract()
        course_item["campusNID"] = "|".join([self.campus_map[x] for x in campus])
        # print(course_item["campusNID"])
        course_brief = response.css(".course-brief").extract_first()
        fees = response.css("div.fees-funding").extract()

        course_item["domesticApplyURL"] = response.urljoin(response.css(".course-brief").css("a.btn-info::attr(href)").extract_first())
        if len(fees) > 0:
            try:
                course_item["domesticFeeTotal"] = re.sub(",","",max(re.findall("\$([,\d]+)",re.findall("<div.(?s)*?(<.(?s)*)</div>", fees[0])[0])))

            except ValueError:
                pass

        aqf = re.findall("AQF\sLevel.*?\d",course_brief)
        if len(aqf) == 1:
            course_item["degreeType"] = aqf[0][-1]

        duration = re.findall("Duration.*?strong>(.*)<",course_brief)
        if len(duration) == 1:
            course_item["durationRaw"] = duration[0]

        rawduration = re.sub("\(.*\)", "", course_item["durationRaw"])
        for i in self.periods.keys():
            if re.search(i, rawduration, re.IGNORECASE):
                course_item["teachingPeriod"] = self.periods[i]
                break

        if "teachingPeriod" in course_item:
            if re.search("max", rawduration, re.IGNORECASE):
                course_item["durationMaxFull"] = re.findall("\d+", rawduration)

            elif "-" in rawduration:
                course_item["durationMaxFull"] = re.findall("-\d+", rawduration)[0]
                course_item["durationMinFull"] = re.findall("\d+-", rawduration)[0]

            else:
                course_item["durationMinFull"] = re.findall("\d+", rawduration)[0]

        study_mode = re.findall("Course Delivery.*?strong>(.*)<",course_brief)
        if len(study_mode) > 0:
            course_item["modeOfStudy"] = study_mode[0]
        holder = []
        if "Face-to-Face" in course_item["modeOfStudy"]:
            holder.append("In person")

        if "Online Mode" in course_item["modeOfStudy"]:
            holder.append("Online")

        course_item["modeOfStudy"] = "|".join(holder)

        course_structure = response.css("div.course-content").extract()
        if len(course_structure) > 0:
            course_item["courseStructure"] = re.findall("<div.(?s)*?(<.(?s)*)</div>",course_structure[0])[0]

        career_path = response.css("div.course-assessed").extract()
        if len(career_path) > 0:
            course_item["careerPathways"] = re.findall("<div.(?s)*?(<.(?s)*)</div>",career_path[0])[0]

        credit = response.css("div.credit-transfer").extract()
        if len(credit) > 0:
            course_item["creditTransfer"] = re.sub("<p.*?>","<p>",re.sub("h\d","strong",re.findall("<h6>.(?s)*?<h6>",re.findall("<div.(?s)*?(<.(?s)*)</div>", credit[0])[0])[0]))

        course_item["entryRequirements"] = response.css("div.entry-requirements").css("p.req-p::text").extract_first()

        # entry = response.css("div.entry-requirements").extract()
        # if len(entry) > 0:
        #     # course_item["entryRequirements"] = entry.css("p.req-p::text").extract_first()
        #     course_item["entryRequirements"] = re.findall("<div.(?s)*?(<.(?s)*)</div>", entry[0])[0]

        intURL = re.sub("/$","",re.sub("^.*\.au","",response.url))+"-int"
        if intURL in self.international:
            self.international.pop(self.international.index(intURL))
            yield response.follow(intURL, callback=self.course_international_parse, meta={'item': course_item})
            return
        else:
            print("no international counterpart")

        yield course_item

    def course_international_parse(self, response):
        course_item = response.meta['item']
        course_brief = response.css(".course-brief").extract_first()

        course_item["internationalApps"] = 1

        course_item["internationalApplyURL"] = response.urljoin(response.css(".course-brief").css("a.btn-info::attr(href)").extract_first())

        fees = response.css("div.fees-funding").extract()
        if len(fees) > 0:
            course_item["internationalFeeTotal"] = re.sub(",", "", re.findall("\$([,\d]+)",re.findall("<div.(?s)*?(<.(?s)*)</div>",fees[0])[0])[0])

        cricos = re.findall("CRICOS Code.*?strong>\\xa0(.*)<", course_brief)
        if len(cricos) == 1:
            course_item["cricosCode"] = cricos[0]

        yield course_item
