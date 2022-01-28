# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *

def master(course_item):
    if "by-research" in course_item["sourceURL"]:
        return "12"
    else:
        if "research" in course_item["overviewSummary"].lower() and "coursework" not in course_item["overviewSummary"].lower():
            return "12"

        elif "research" not in course_item["overviewSummary"].lower() and "coursework" in course_item["overviewSummary"].lower():
            return "11"

        elif "research" not in course_item["overviewSummary"].lower() and "coursework" not in course_item["overviewSummary"].lower():
            # course_item.add_flag("degreeType", "Master degree description has no indicator")
            return "11"
        else:
            # course_item.add_flag("degreeType", "Both indicators present")
            return "11"

def bachelor(course_item):
    if "doubleDegree" in course_item:
        if course_item["doubleDegree"] == 1:
            index = 1 if "degreeType" in course_item else 0
            if "honour" in course_item["rawStudyfield"][index]:
                return "3"
            else:
                return "2"

    elif "honour" in course_item["courseName"].lower():
        return "3"

    else:
        return "2"


class EcuSpiderSpider(scrapy.Spider):
    name = 'ecu_spider'
    start_urls = [
        'https://www.ecu.edu.au/degrees/courses?query=&profile=collapsing&collection=ecu-fs-courses&form=courses&start_rank=1'
    ]

    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []  # ["https://www.ecu.edu.au/degrees/courses/graduate-certificate-of-extended-care-paramedicine", "https://www.ecu.edu.au/degrees/courses/bachelor-of-arts-bachelor-of-media-and-communication", "https://www.ecu.edu.au/degrees/courses/associate-degree-in-criminology-and-justice"]

    institution = "Edith Cowan University (ECU)"
    uidPrefix = "AU-ECU-"

    degrees = {
        "master": master,
        "bachelor": bachelor,
        "advanced diploma": "5",
        "certificate iv": "4",
        "undergraduate certificate": "4"
    }

    campus = {
        "Joondalup": "589",
        "South West(Bunbury)": "585",
        "South West (Bunbury)": "585",
        "Mount Lawley": "588"
    }

    def parse(self, response):
        courses = response.css('.card')
        next_page = response.css("a[title='Next Page']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        for course in courses:
            course_link = course.css("a::attr(href)").extract_first()
            fields = {}
            fields["name"] = course.css("a::text").extract_first()
            description = course.css("p::text").extract_first()
            fields["description"] = cleanspace(description)
            items = course.css("li")
            for item in items:
                key = item.css("span::text").extract_first().strip(":")
                value = item.css("li::text").extract_first()
                fields[key] = value
            # print(fields)
            if course_link not in self.blacklist_urls and course_link not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course_link in self.superlist_urls) or len(self.superlist_urls) == 0:
                    yield response.follow(course_link, callback=self.course_parse, meta={'fields': fields})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_item["courseName"] = response.meta["fields"]["name"]
        course_item["uid"] = self.uidPrefix + course_item["courseName"]
        course_item["courseCode"] = cleanspace(response.meta["fields"]["Code"])
        # Test course name
        pattern = "^\w+?\s-\s.*$"
        if re.search(pattern, course_item["courseName"]):
            course_item["courseName"] = course_item["courseName"].split(" - ")[-1]

        course_item["overviewSummary"] = response.meta["fields"]["description"]
        course_item.set_sf_dt(self.degrees)
        
        course_item["overview"] = "".join(response.css(".heroBanner__intro .bannerContent--wide p:not(.heroBanner__courseCode)").extract())

        # Fees
        domestic_fee = response.css(".audience__panel--domestic p.base__subheading::text").extract_first()
        domestic_text = "".join(response.css("#feesScholarships .audience__panel--domestic p::text").extract())
        international_fee = response.css(".audience__panel--international p.base__subheading::text").extract_first()
        international_text = "".join(response.css("#feesScholarships .audience__panel--international p::text").extract())
        if domestic_fee:
            domestic_fee = re.findall("\$([\d,]+)", domestic_fee)[0].replace(",", "")
            if "estimated 1st year indicative fee" in domestic_text:
                course_item["domesticFeeAnnual"] = domestic_fee
            else:
                course_item.add_flag("domesticFeeAnnual", "non annual fee")
        if international_fee:
            international_fee = re.findall("\$([\d,]+)", international_fee)[0].replace(",", "")
            if "estimated 1st year indicative fee" in international_text:
                course_item["internationalFeeAnnual"] = international_fee
            else:
                course_item.add_flag("internationalFeeAnnual", "non annual fee")

        # Duration
        duration = response.meta["fields"]["Duration"]
        full_time = re.findall("([\d\.]+)\sYears? Full-time", duration)
        part_time = re.findall("([\d\.]+)\sYears? Part-time", duration)
        course_item["durationMinFull"] = full_time[0] if full_time else None
        course_item["durationMinPart"] = part_time[0] if part_time else None
        if course_item["durationMinFull"]:
            course_item["teachingPeriod"] = 1

        # Campus
        campuses = [cleanspace(x) for x in response.meta["fields"]["Location"].split(", ")]
        modes = []
        holder = []
        if "Off Campus" in campuses:
            modes.append("Online")
        for campus in [x for x in campuses if x != "Off Campus"]:
            if campus in list(self.campus.keys()):
                holder.append(self.campus[campus])
            else:
                course_item.add_flag("campusNID", "No match for campus name: "+campus)
        if holder:
            modes.append("In person")
            course_item["campusNID"] = "|".join(holder)

        if modes:
            course_item["modeOfStudy"] = "|".join(modes)

        cricos = response.xpath("//div[contains(@class, 'quickReference__item') and contains(.//h3, 'CRICOS code')]//span/text()").get()
        if cricos:
            course_item["cricosCode"] = cleanspace(cricos)
            course_item["internationalApps"] = 1
            course_item["internationalApplyURL"] = response.request.url

        jobs = response.xpath("//p[preceding-sibling::h3/text()='Possible future job titles']/text()").get()
        if jobs:
            course_item["careerPathways"] = jobs

        what_learn = response.xpath("//ol[@class='learning-outcome-list']/li/text()").getall()
        if what_learn:
            what_learn = "\n".join(["<li>" + x + "</li>" for x in what_learn])
            course_item["whatLearn"] = "<ul>\n"+what_learn+"\n</ul>"
        # if "flag" in course_item:
        yield course_item