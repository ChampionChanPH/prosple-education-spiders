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


class UomSpiderSpider(scrapy.Spider):
    name = 'uom_spider'
    allowed_domains = ['study.unimelb.edu.au', 'unimelb.edu.au']
    start_urls = ['https://study.unimelb.edu.au/find/']
    banned_urls = []
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    institution = "University of Melbourne"
    uidPrefix = "AU-UOM-"

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

    campuses = {
        "Werribee": "762",
        "Hawthorn": "761",
        "Creswick": "759",
        "Burnley": "758",
        "Dookie": "760",
        "Southbank": "756",
        "Off Campus": "757",
        "Melbourne": "754",
        "Parkville": "753"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "senior executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "doctoral program": "6",
        "certificate": "4",
        "specialist certificate": "4",
        "professional certificate": "14",
        "certificate i": "4",
        "certificate ii": "4",
        "certificate iii": "4",
        "certificate iv": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
        "juris doctor": "10",
        "non-award": "13",
        "no match": "15"
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

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        categories = response.xpath("//div[@data-test='interest-list']//a[@data-test='interest-item']/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//div[@data-test='course-list']//a[@data-test='card-course']/@href").getall()

        for item in courses:
            if not re.search("/(major|specialisation|minor)/", item):
                yield SplashRequest(response.urljoin(item), callback=self.course_parse, args={'wait': 10},
                                    meta={'url': response.urljoin(item)})

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.meta["url"]
        course_item["published"] = 1
        course_item["institution"] = self.institution

        course_name = response.xpath(
            "//h1[@data-test='header-course-title' or @data-test='course-header-title']/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[@data-test='course-overview-content']/*").getall()
        if overview:
            if re.search("^<div><div", overview[0]):
                overview = response.xpath("//div[@data-test='course-overview-content']/*/*/*").getall()
            elif re.search("^<div><p", overview[0]) or re.search("^<section", overview[0]):
                overview = response.xpath("//div[@data-test='course-overview-content']/*/*").getall()
        holder = []
        for index, item in enumerate(overview):
            if not re.search("^<(p|u|o)", item) and index != 0:
                break
            elif re.search("notice--default", item):
                pass
            else:
                holder.append(item)
        if holder:
            summary = [strip_tags(x) for x in holder]
            course_item.set_summary(' '.join(summary))
            course_item['overview'] = strip_tags(''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        cricos = response.xpath("//li[contains(text(), 'CRICOS')]/*/text()").get()
        if cricos:
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1

        lowest_atar = response.xpath("//dt[contains(*/text(), 'Lowest Selection Rank')]/following-sibling::dd/*["
                                     "contains(@class, 'score-panel__value-heading')]").get()
        if lowest_atar:
            lowest_atar = re.findall('\d{2}\.\d{2}', lowest_atar, re.M)
            lowest_atar = [float(x) for x in lowest_atar]
            if lowest_atar:
                lowest_atar = min(lowest_atar)

        guaranteed_score = response.xpath(
            "//div[contains(strong/text(), 'Guaranteed ATAR')]/following-sibling::*").get()
        if guaranteed_score:
            guaranteed_score = re.findall('\d{2}\.\d{2}', guaranteed_score, re.M)
            guaranteed_score = [float(x) for x in guaranteed_score]
            if guaranteed_score:
                guaranteed_score = min(guaranteed_score)

        if lowest_atar and guaranteed_score:
            course_item['guaranteedEntryScore'] = guaranteed_score
            course_item['lowestScore'] = lowest_atar
        elif lowest_atar and not guaranteed_score:
            course_item['guaranteedEntryScore'] = lowest_atar
        elif not lowest_atar and guaranteed_score:
            course_item['guaranteedEntryScore'] = guaranteed_score

        fee = response.xpath("//*[contains(text(), 'Indicative total course fee')]/preceding-sibling::*/text()").get()
        if fee:
            total_fee = re.findall("\d*,?\d{3}", fee, re.M)
            if total_fee:
                total_fee = re.sub(",", "", total_fee[0])
                course_item["domesticFeeTotal"] = float(total_fee)

        duration = response.xpath("//li[@id='course-overview-duration']/text()").getall()
        if duration:
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\spart.time)",
                                       duration, re.I | re.M | re.DOTALL)
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
                                           duration,
                                           re.I | re.M | re.DOTALL)
                if duration_full:
                    if len(duration_full) == 1:
                        course_item["durationMinFull"] = float(duration_full[0][0])
                        self.get_period(duration_full[0][1].lower(), course_item)
                    if len(duration_full) == 2:
                        course_item["durationMinFull"] = min(float(duration_full[0][0]), float(duration_full[1][0]))
                        course_item["durationMaxFull"] = max(float(duration_full[0][0]), float(duration_full[1][0]))
                        self.get_period(duration_full[1][1].lower(), course_item)

        location = response.xpath("//li[@id='course-overview-campus']/text()").get()
        if location:
            study_holder = set()
            campus_holder = set()
            if re.search('online', location, re.M | re.I):
                study_holder.add("Online")
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.add(self.campuses[campus])
                    study_holder.add("In Person")
            if study_holder:
                course_item["modeOfStudy"] = "|".join(study_holder)
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        entry = response.xpath(
            "//*[contains(text(), 'Prerequisites') or contains(text(), 'Pre-requisites')]/following-sibling::*").get()
        if entry:
            course_item["entryRequirements"] = strip_tags(entry, remove_all_tags=False, remove_hyperlinks=True)

        period = response.xpath("//li[@id='course-overview-entryPeriods']/text()").get()
        if period:
            start_holder = []
            for month in self.months:
                if re.search(month, period, re.M):
                    start_holder.append(self.months[month])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        course_item.set_sf_dt(self.degrees, degree_delims=["and", "/"])

        learn = response.xpath("//*[text()='LEARNING OUTCOMES']/following-sibling::*").get()
        if learn:
            course_item["whatLearn"] = strip_tags(learn, remove_all_tags=False, remove_hyperlinks=True)

        learn = response.xpath("//a[@data-test='nav-link-what-will-i-study']/@href").get()

        if response.xpath("//*[contains(text(), 'Page not found')]").getall():
            pass
        else:
            if learn:
                yield response.follow(learn, callback=self.learn_parse, meta={'item': course_item})
            else:
                yield course_item

    def learn_parse(self, response):
        course_item = response.meta['item']

        learn = response.xpath("//div[@class='course-content']/*").getall()
        holder = []
        for item in learn:
            if not re.search("^<p", item) and not re.search("^<ul", item) and not re.search("^<div><p", item) and \
                    learn.index(item) != 0:
                break
            elif re.search("notice--default", item):
                pass
            else:
                holder.append(strip_tags(item, False))
        if holder:
            course_item["whatLearn"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        career = response.xpath("//a[@data-test='nav-link-where-will-this-take-me']/@href").get()

        if career:
            yield response.follow(career, callback=self.career_parse, meta={'item': course_item})
        else:
            yield course_item

    def career_parse(self, response):
        course_item = response.meta['item']

        career = response.xpath("//div[@class='course-content']/*").getall()
        holder = []
        for item in career:
            if not re.search("^<p", item) and not re.search("^<ul", item) and not re.search("^<div><p", item) and \
                    career.index(item) != 0:
                break
            elif re.search("notice--default", item):
                pass
            else:
                holder.append(strip_tags(item, False))
        if holder:
            course_item["careerPathways"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath("//a[@data-test='nav-link-how-to-apply']/@href").get()

        if apply:
            yield response.follow(apply, callback=self.apply_parse, meta={'item': course_item})
        else:
            yield course_item

    def apply_parse(self, response):
        course_item = response.meta['item']

        apply = response.xpath("//div[contains(@class, 'course-content')]/*").getall()
        holder = []
        for item in apply:
            if not re.search("^<p", item) and not re.search("^<ul", item) and not re.search("^<div><p", item) and \
                    apply.index(item) != 0:
                break
            elif re.search("notice--default", item):
                pass
            else:
                holder.append(strip_tags(item, False))
        if holder:
            course_item["howToApply"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        yield course_item