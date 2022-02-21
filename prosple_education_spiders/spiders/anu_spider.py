# -*- coding: utf-8 -*-
# by: Johnel Bacani

from ..standard_libs import *
from ..scratch_file import *


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


class AnuSpiderSpider(scrapy.Spider):
    name = 'anu_spider'
    # allowed_domains = ['https://programsandcourses.anu.edu.au/catalogue']
    start_urls = ['https://programsandcourses.anu.edu.au/catalogue']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = [
        "https://programsandcourses.anu.edu.au/2020/program/5050XNAWD",
        "https://programsandcourses.anu.edu.au/2021/program/1302XNAWD",
        'https://programsandcourses.anu.edu.au/2021/program/5035XJOINT',
        'https://programsandcourses.anu.edu.au/2021/program/5034XNAWD',
        'https://programsandcourses.anu.edu.au/2021/program/5082XCRWFD',
        'https://programsandcourses.anu.edu.au/2021/program/1305XGSPU',
        'https://programsandcourses.anu.edu.au/2021/program/5036XGSPP',
        'https://programsandcourses.anu.edu.au/2021/program/5031XNAWD',
        'https://programsandcourses.anu.edu.au/2021/program/1152XNAWD'
    ]
    scraped_urls = []
    superlist_urls = []

    institution = "Australian National University (ANU)"
    uidPrefix = "AU-ANU-"

    degrees = {
        'doctor': '6',
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "postgraduate certificate": "7",
        "undergraduate certificate": "4",
        "postgraduate diploma": "8",
        "artist diploma": "5",
        "non-award": "13",
        "non award": "13",
        "juris doctor (honours)": "10",
        "flexible double masters": "11",
        "flexible double degree": "2",
        "graduate non-award": "8",  # assigning a graduate type to get right course level then just assign non-award override after
        # "foundation certificate": "4"
    }

    custom_lua = """
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(3))
      a = 1
      while(a < 5)
      do
        a = a + 1
        local element = splash:select('a[data-template="program-template"]')
        assert(element:mouse_click())
        assert(splash:wait(5))
      end
      return {
        html = splash:html(),
        png = splash:png(),
        har = splash:har(),
      }
    end
    """
    
    def parse(self, response):
        yield SplashRequest(
            response.request.url,
            self.course_catalog,
            endpoint='execute',
            args={'lua_source': self.custom_lua, 'url': response.request.url},
            meta={'url': response.request.url}
        )

    def course_catalog(self, response):
        courses = response.css("table.catalogue-search-results__table tbody tr")
        for row in courses:
            cells = row.css("td")
            code = cleanspace(cells[0].css("td a::text").get())
            course = r"https://programsandcourses.anu.edu.au" + cells[0].css("td a::attr(href)").get()
            name = cleanspace(cells[1].css("td a::text").get())
            level = cleanspace(cells[3].css("td::text").get())
            duration = cleanspace(cells[5].css("td::text").get())
            study_mode = cleanspace(cells[6].css("td::text").get())
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield SplashRequest(
                        course,
                        callback=self.course_parse,
                        args={'wait': 3},
                        meta={
                            'code': code,
                            'name': name,
                            'level': level,
                            'duration': duration,
                            'study_mode': study_mode,
                            'url': course
                        }
                    )

    def course_parse(self, response):
        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.meta["url"]

        course_item["campusNID"] = "569"

        name = re.sub("<.*?>", "", response.meta['name'])
        if name:
            course_item.set_course_name(name, self.uidPrefix)
        course_item.set_sf_dt(self.degrees, type_delims=["of", "in", "-"])

        atar = response.xpath("//abbr[@title='Australian Tertiary Admission Rank']/following-sibling::*/text()").get()
        if atar:
            try:
                course_item['guaranteedEntryScore'] = int(atar)
            except ValueError:
                pass

        code = response.meta["code"]
        if code:
            course_item["courseCode"] = code

        study_mode = response.meta["study_mode"]
        if study_mode:
            if study_mode == "In Person":
                course_item["modeOfStudy"] = "In person"

            elif study_mode == "Online":
                course_item["modeOfStudy"] = "Online"

            elif study_mode == "Multi-Modal":
                course_item["modeOfStudy"] = "In person|Online"

            else:
                course_item.add_flag("modeOfStudy", "New keyword found: " + study_mode)

        overview = response.xpath("//div[@id='introduction']/*").getall()
        if not overview:
            overview = response.xpath("//*[@id='further-info']/following-sibling::text()").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        int_fee = response.css("div#indicative-fees__international dd::text").get()
        if int_fee:
            fee = re.findall("[\d\.,]+", int_fee)
            if fee:
                course_item["internationalFeeTotal"] = fee[0].replace(",", "")

        cricos = response.xpath("//span[preceding-sibling::span/text()='CRICOS code']/text()").get()
        if cricos:
            if cricos != "NO CRICOS":
                course_item["cricosCode"] = cleanspace(cricos)
                course_item["internationalApps"] = 1

        duration = response.meta["duration"]
        if duration:
            duration = float(duration)
            course_item["teachingPeriod"] = 1
            course_item["durationMinFull"] = duration

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"], type_delims=["of", "in", "by"])

        if 'teachingPeriod' in course_item and 'durationMinFull' in course_item and \
                ((course_item['teachingPeriod'] == 1 and course_item['durationMinFull'] <= 0.5) or
                 (course_item['teachingPeriod'] == 12 and course_item['durationMinFull'] <= 6)):
            if 'degreeType' in course_item and course_item['degreeType'] == '13':
                course_item['degreeType'] = '16'

        # if "flag" in course_item:
        if not re.search('Non.Award', course_item['courseName'], re.I | re.DOTALL) and \
                not re.search('Scholarship', course_item['courseName'], re.I):
            yield course_item

