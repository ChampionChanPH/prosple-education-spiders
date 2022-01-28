import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


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


class UocSpiderSpider(scrapy.Spider):
    name = 'uoc_spider'
    allowed_domains = ['search.canberra.edu.au', 'www.canberra.edu.au', 'canberra.edu.au']
    start_urls = ['https://search.canberra.edu.au/s/search.html?collection=courses&form=course-search&profile'
                  '=_default&query=!padre&course-search-widget__submit=&meta_C_and=COURSE&sort=metaH&f.Type|B'
                  '=undergraduate&f.Course+Status%7CD=Open',
                  'https://search.canberra.edu.au/s/search.html?collection=courses&form=course-search&profile'
                  '=_default&query=!padre&course-search-widget__submit=&meta_C_and=COURSE&sort=metaH&f.Course+Status'
                  '%7CD=Open&f.Type|B=postgraduate',
                  'https://search.canberra.edu.au/s/search.html?collection=courses&form=course-search&profile'
                  '=_default&query=!padre&course-search-widget__submit=&meta_C_and=COURSE&sort=metaH&f.Course+Status'
                  '%7CD=Open&f.Type|B=research']
    courses = []

    degrees = {"graduate certificate": "7",
               "graduate diploma": "8",
               "master": research_coursework,
               "bachelor": bachelor_honours,  # One course "Honours in Information Sciences" not captured, manually
               # updated
               "doctor": "6",
               "certificate": "4",
               "diploma": "5",
               "associate degree": "1",
               "university foundation studies": "13",
               "non-award": "13",  # "University of Canberra International Foundation Studies" not captured, manually
               # updated
               "no match": "15"
               }

    campuses = {
        "Singapore": "738",
        "Canberra": "735",
        "Sydney": "737"
    }

    def parse(self, response):
        self.courses.extend(response.xpath("//table[@class='table course_results']//tr/@data-fb-result").getall())

        next_page = response.xpath("//ul[@class='pagination pagination-lg']/li/a[@rel='next']/@href").get()

        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

        for course in self.courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of Canberra"
        uidPrefix = "AU-UOC-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        course_name, course_code = re.split(r" - ", response.xpath("//h1[@class='course_title']/text()").get())
        course_item["courseName"] = course_name
        course_item["courseCode"] = course_code
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        cricos = response.xpath("//table[@class='course-details-table']//tr/th[contains(text(), "
                                "'CRICOS')]/following-sibling::td").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos)
            if len(cricos) > 0:
                course_item["cricosCode"] = cricos[0]
                course_item["internationalApps"] = 1

        campus_holder = []
        location = response.xpath("//table[@class='course-details-table']//tr/th[contains(text(), "
                                  "'Location')]/following-sibling::td").get()
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(set(campus_holder))

        course_item.set_sf_dt(self.degrees)

        career = response.xpath("//div[@id='introduction']/h2[contains(text(), 'Career "
                                "opportunities')]/following-sibling::ul").get()
        if career is not None:
            course_item["careerPathways"] = career

        overview = response.xpath("//div[@id='introduction']//h2[contains(text(), 'Study a')]/preceding::p").getall()
        if len(overview) == 0:
            overview = response.xpath("//div[@id='introduction']/h2[contains(text(), "
                                      "'Introduction')]/following-sibling::p").getall()
            if len(overview) > 0:
                overview = "".join(overview)
                course_item["overview"] = strip_tags(overview, False)
        else:
            overview = "".join(overview)
            course_item["overview"] = strip_tags(overview, False)

        learn = response.xpath("//div[@id='introduction']//h2[contains(text(), 'Study "
                               "a')]/following-sibling::ul").get()
        if learn is not None:
            course_item["whatLearn"] = learn

        for header, content in zip(response.xpath("//div[@id='fees']//table//tr/th/text()").getall(),
                                   response.xpath("//div[@id='fees']//table//tr/td/text()").getall()):
            if re.search("domestic", header, re.I):
                dom_fee = re.findall("\$(\d+),?(\d{3})", content)
                if len(dom_fee) > 0:
                    course_item["domesticFeeAnnual"] = "".join(dom_fee[0])
            if re.search("international", header, re.I):
                int_fee = re.findall("\$(\d+),?(\d{3})", content)
                if len(int_fee) > 0:
                    course_item["internationalFeeAnnual"] = "".join(int_fee[0])

        entry = response.xpath("//div[@id='admission']/h2[contains(text(), 'Admission')]/following-sibling::p[1]").get()
        if entry is not None:
            course_item["entryRequirements"] = entry

        yield course_item