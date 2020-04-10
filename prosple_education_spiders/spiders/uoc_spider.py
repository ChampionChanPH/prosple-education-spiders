import scrapy
import re
from ..items import Course
from ..scratch_file import strip_tags
from datetime import date


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

    def parse(self, response):
        # self.courses.extend(response.xpath("//table[@class='table course_results']//tr/@data-fb-result").getall())
        #
        # next_page = response.xpath("//ul[@class='pagination pagination-lg']/li/a[@rel='next']/@href").get()
        #
        # if next_page is not None:
        #     yield response.follow(next_page, callback=self.parse)

        courses = ["https://www.canberra.edu.au/coursesandunits/course?course_cd=MGB302&version_number=1&title"
                   "=Bachelor-of-Commerce-(Business-Economics)&location=BRUCE&rank=AAA&faculty=Faculty-of-Business,"
                   "-Government---Law&year=2020",
                   "https://www.canberra.edu.au/coursesandunits/course?course_cd=142JA&version_number=3&title"
                   "=Bachelor-of-Applied-Science-in-Forensic-Studies&location=BRUCE&rank=AAA&faculty=Faculty-of"
                   "-Science-and-Technology&year=2020",
                   "https://www.canberra.edu.au/coursesandunits/course?course_cd=910AA&version_number=2&title=Master"
                   "-of-Applied-Science-(Research)&location=BRUCE&rank=FFF&faculty=Faculty-of-Science-and-Technology"
                   "&year=2020",
                   "https://www.canberra.edu.au/coursesandunits/course?course_cd=723AL&version_number=3&title=Master"
                   "-of-Business-Administration-(Bhutan)&location=RIM-BHUTAN&rank=CCC&faculty=Faculty-of-Business,"
                   "-Government---Law&year=2020",
                   "https://www.canberra.edu.au/coursesandunits/course?course_cd=MGB001&version_number=1&title"
                   "=Bachelor-of-Accounting&location=BRUCE&rank=AAA&faculty=Faculty-of-Business,"
                   "-Government---Law&year=2020"]

        for course in courses:
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

        cricos = response.xpath("//table[@class='course-details-table']//tr/th[contains(text(), "
                                "'CRICOS')]/following-sibling::td").get()
        if cricos is not None:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos)
            if len(cricos) > 0:
                course_item["cricosCode"] = cricos[0]

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
