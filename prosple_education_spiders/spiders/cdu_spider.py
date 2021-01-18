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

class CduSpiderSpider(scrapy.Spider):
    name = 'cdu_spider'
    # allowed_domains = ['https://www.cdu.edu.au/course-search']
    start_urls = ['https://www.cdu.edu.au/course-search/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "https://www.cdu.edu.au/study/ueess00092-restricted-attachment-cordscables-and-plugs-low-voltage-three-phase-electrical-0",
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "Charles Darwin University (CDU)"
    uidPrefix = "AU-CDU-"

    degrees = {
        "master": "11",
        "master by research": "12",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "bachelor": bachelor,
        "undergraduate certificate": "4",
        # "postgraduate certificate": "7",
        # "postgraduate diploma": "8",
        # "artist diploma": "5",
        # "foundation certificate": "4"
    }

    campuses = {
        "casuarina": "519",
        "casuarina campus": "519",
        "batchelor": "520",
        "alice springs": "521",
        "alice springs campus": "521",
        "dpc alice springs (desert peoples centre)": "521",
        "melbourne": "11714",
        "palmerston": "22177",
        "tennant creek": "523",
        "katherine": "522",
        "sydney": "518",
        "cdu sydney": "518",
        "waterfront": "517",
        "waterfront darwin": "517",
        "cdu waterfront darwin": "517",
        "darwin": "515",
        "jabiru": "0",
        "nhulunbuy": "0",
        "yulara": "0",
    }

    def parse(self, response):
        course_rows = response.css(".js-shortlist div.fable__row")

        for row in course_rows:
            course = row.css("a::attr(href)").get()

            campus = row.css(".course-list__locations span::text").getall()
            campus = [cleanspace(x).lower() for x in campus]

            durations = row.css(".flex-15 div[data-student-type='domestic'] div::text").getall()
            durations = [cleanspace(x).lower() for x in durations]
            # print(durations)
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse, meta={"campus": campus, "durations": durations})

        next_page = response.css("li.pagination__next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        # course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            name = cleanspace(name)

            if re.findall("\d", name.split(" ")[0]):
                course_item["courseCode"] = name.split(" ")[0]
                name = re.sub("^.*?\s", "", name)


            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees)
        if "(Postgraduate Studies)" in course_item["courseName"]:
            course_item["courseLevel"] = "2"
            course_item["group"] = 4
            course_item["canonicalGroup"] = "PostgradAustralia"

        campus = response.meta["campus"]
        if campus:
            holder = []
            mode_holder = []
            for i in campus:
                if i in list(self.campuses.keys()):
                    holder.append(self.campuses[i])
                    mode_holder.append("In person")

                elif i in ["online", "remote"]:
                    mode_holder.append("Online")

                else:
                    course_item.add_flag("campusNID", "Unrecognized campus name: "+i)

            if mode_holder:
                course_item["modeOfStudy"] = "|".join(list(set(mode_holder)))

            if holder:
                course_item["campusNID"] = "|".join(list(set(holder)))

        overview = response.css("div.field-course-overview .field-item p::text").getall()
        if overview:
            course_item["overview"] = cleanspace("\n".join(overview))
            course_item.set_summary(cleanspace(" ".join(overview)))

        durations = response.meta["durations"]
        if durations:
            for i in durations:
                value = re.findall("[\d\.]+", i)
                if value:
                    if "part-time" in i:
                        course_item["durationMinPart"] = value[0]
                    else:
                        course_item["durationMinFull"] = value[0]

                    if "year" in i:
                        course_item["teachingPeriod"] = 1
                    else:
                        course_item.add_flag("teachingPeriod", "No teaching period found: " + i)

        domestic_fee = response.css(".field-vet-other-fees p").get()
        if domestic_fee:
            fees = re.findall("\$(\d*)[,\s]?(\d+)(\.\d\d)?", domestic_fee, re.M)
            fees = [float(''.join(x)) for x in fees]
            if fees:
                course_item["domesticFeeTotal"] = max(fees)

        code = response.xpath("//div[preceding-sibling::div/text()='CDU Course Code']//p/text()").get()
        if code:
            course_item["courseCode"] = cleanspace(code)

        entryRequirements = response.css("#course-entry-requirements p::text").getall()
        if entryRequirements:
            course_item["entryRequirements"] = "\n".join(entryRequirements)

        international = response.css("span.shortlist__not-available::text").get()
        if international:
            if international != "Not available to international students.":
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url


        # if "flag" in course_item:
        yield course_item
