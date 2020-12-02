# -*- coding: utf-8 -*-
# by Christian Anasco

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


class MuSpiderSpider(scrapy.Spider):
    name = 'mu_spider'
    allowed_domains = ['www.massey.ac.nz', 'massey.ac.nz']
    start_urls = ['https://www.massey.ac.nz/massey/learning/programme-course/programme-list.cfm']
    banned_urls = []
    institution = 'Massey University'
    uidPrefix = 'NZ-MU-'

    campuses = {
        "Auckland": "52524",
        "Manawatū": "52525",
        "Wellington": "52526",
        "Distance Learning": "52527"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "foundation certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "non-award": "13",
        "no match": "15",
        'te aho paerewa postgraduate diploma': '8',
        'postgraduate diploma': '8',
        'postgraduate certificate': '7',
        'te aho tātairangi: bachelor': bachelor_honours
    }

    teaching_periods = {
        "year": 1,
        "semester": 2,
        "trimester": 3,
        "quarter": 4,
        "month": 12,
        "week": 52,
        "day": 365
    }

    months = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        courses = response.xpath("//div[@id='prog-list']//a/@href").getall()

        for item in courses:
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item['lastUpdate'] = date.today().strftime("%m/%d/%y")
        course_item['sourceURL'] = response.request.url
        course_item['published'] = 1
        course_item['institution'] = self.institution
        course_item['domesticApplyURL'] = response.request.url

        course_name = response.xpath("//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//h2[contains(text(), 'What is it like?')]/following-sibling::div["
                                  "@class='progSectionText']/div[@class='progSectionText']/*").getall()
        if overview:
            holder = []
            for index, item in enumerate(overview):
                if index == 0:
                    item = re.sub("<img.*?>", "", item, re.DOTALL)
                    holder.append(item)
                elif not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M):
                    break
                elif strip_tags(item).strip() != '':
                    item = re.sub("<img.*?>", "", item, re.DOTALL)
                    holder.append(item)
            if holder:
                if not re.search("^<p", holder[0], re.M) and not re.search("^<ul", holder[0], re.M):
                    if len(holder) > 1:
                        course_item.set_summary(strip_tags(holder[1]))
                        course_item["overview"] = strip_tags("".join(holder), remove_all_tags=False,
                                                             remove_hyperlinks=True)
                    else:
                        course_item.set_summary(strip_tags(holder[0]))
                        course_item["overview"] = strip_tags("".join(holder), remove_all_tags=False,
                                                             remove_hyperlinks=True)
                else:
                    course_item.set_summary(strip_tags(holder[0]))
                    course_item["overview"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//*[contains(text(), 'What will you learn')]/following-sibling::*").getall()
        if learn:
            holder = []
            for item in learn:
                if not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M):
                    break
                elif strip_tags(item).strip() != '' and not re.search("<img", item, re.M):
                    holder.append(item)
            if holder:
                course_item["whatLearn"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//h2[@class='progSectionTitle'][contains(text(), 'Careers')]/following-sibling::div["
                                "@class='progSectionText']/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags("".join(career), remove_all_tags=False, remove_hyperlinks=True)

        key_facts = response.xpath("//ul[@class='key-facts-list']").getall()
        if key_facts:
            key_facts = ", ".join(key_facts)
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, key_facts, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)
            if re.search("(?<!not\s)available for international students", key_facts, re.I | re.M):
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       key_facts, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
                                       key_facts, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                if len(duration_full[0]) == 2:
                    course_item["durationMinFull"] = float(duration_full[0][0])
                    self.get_period(duration_full[0][1].lower(), course_item)
                if len(duration_full[0]) == 3:
                    course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[0][1]))
                    course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[0][1]))
                    self.get_period(duration_full[0][2].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]
            if "durationMinFull" not in course_item and "durationMinPart" not in course_item:
                duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
                                           key_facts, re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by', 'for'])

        course_item['group'] = 2
        course_item['canonicalGroup'] = 'GradNewZealand'

        planning_link = response.xpath("//a[i[@class='nav-icon-planning']]/@href").get()
        if not re.search("not currently accepting applications", key_facts, re.I | re.M):
            if planning_link:
                yield response.follow(planning_link, callback=self.planning_parse, meta={'item': course_item})
            else:
                yield course_item

    def planning_parse(self, response):
        course_item = response.meta['item']

        entry = response.xpath("//h2[@class='progSectionTitle'][contains(text(), 'Entry "
                               "requirements')]/following-sibling::div[@class='progSectionText'][1]/*").getall()
        if entry:
            holder = []
            for index, item in enumerate(entry):
                if index == 0:
                    item = re.sub("<img.*?>", "", item, re.DOTALL)
                    holder.append(item)
                elif not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M):
                    break
                elif strip_tags(item).strip() != '':
                    item = re.sub("<img.*?>", "", item, re.DOTALL)
                    holder.append(item)
            if holder:
                course_item["entryRequirements"] = strip_tags("".join(holder), remove_all_tags=False,
                                                              remove_hyperlinks=True)

        yield course_item
