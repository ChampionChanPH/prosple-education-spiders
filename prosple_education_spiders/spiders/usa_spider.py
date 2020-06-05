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
    if "durationMinFull" in course_item:
        if course_item["teachingPeriod"] == 1:
            if float(course_item["durationMinFull"]) < 1:
                course_item[field_to_update] = course_item[field_to_use]
            else:
                course_item[field_to_update] = float(course_item[field_to_use]) * float(course_item["durationMinFull"])


class UsaSpiderSpider(scrapy.Spider):
    name = 'usa_spider'
    allowed_domains = ['study.unisa.edu.au', 'online.unisa.edu.au']
    start_urls = ['https://study.unisa.edu.au/']
    banned_urls = ['https://study.unisa.edu.au/careers/31/',
                   'https://online.unisa.edu.au/']
    institution = "University of South Australia"
    uidPrefix = "AU-USA-"

    campuses = {
        "Magill": "780",
        "Mt Gambier": "784",
        "City West": "781",
        "City East": "782",
        "Mawson Lakes": "783",
        "Whyalla": "785",
        "Adelaide": "786"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "international master": research_coursework,
        "masters": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "advanced diploma": "5",
        "diploma": "5",
        "associate degree": "1",
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
        categories = response.xpath("//div[contains(@class, 'online-degree-panel')]/a/@href").getall()

        for item in categories:
            yield response.follow(item, callback=self.sub_parse)

    def sub_parse(self, response):
        courses = response.xpath("//table[contains(@class, 'degree-list-table')]//a/@href").getall()

        for item in courses:
            item = re.sub("\?audience.*", "", item, re.DOTALL | re.I)
            item = re.sub("/$", "", item)
            yield response.follow(item, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//div[@class='content']//h1/text()").get()
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//div[contains(div/*/text(), 'Degree overview')]/following-sibling::div//ul").get()
        if overview:
            course_item["overview"] = strip_tags(overview.strip(), False)

        summary = response.xpath("//span[contains(@id, 'why') and contains(@id, "
                                 "'degree')]/following-sibling::div/p/text()").get()
        if summary:
            course_item.set_summary(summary.strip())

        learn = response.xpath("//*[contains(text(), 'What you') and contains(text(), 'learn')]/following-sibling::div").getall()
        if learn:
            course_item["whatLearn"] = strip_tags("".join(learn), False)

        career = response.xpath("//div[contains(div/span/@id, 'yourcareer')]/following-sibling::div/div/div/div/*").getall()
        if career:
            course_item["careerPathways"] = strip_tags("".join(career), False)

        start = response.xpath("//p[contains(span/text(), 'Start')]//text()").getall()
        if start:
            start = [x.strip() for x in start]
            start = "".join(start)
            start_holder = []
            for item in self.months:
                if re.search(item, start, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        location = response.xpath("//p[contains(span/text(), 'Campus')]//text()").getall()
        if location:
            location = [x.strip() for x in location]
            location = "".join(location)
            campus_holder = []
            for campus in self.campuses:
                if re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        study_holder = []
        online = response.xpath("//p[contains(span/text(), 'Mode')]//text()").getall()
        if online:
            online = [x.strip() for x in online]
            online = "".join(online)
            if re.search("online", online, re.I | re.M):
                study_holder.append("Online")
        if "campusNID" in course_item:
            study_holder.append("In Person")
        if study_holder:
            course_item["modeOfStudy"] = "|".join(study_holder)

        duration = response.xpath("//p[contains(span/text(), 'Duration')]//text()").getall()
        if duration:
            duration = [x.strip() for x in duration]
            duration = "".join(duration)
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\("
                                       "?s?\)?\s?full.time)", duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)\("
                                       "?s?\)?\s?part.time)", duration, re.I | re.M | re.DOTALL)
            if not duration_full and duration_part:
                self.get_period(duration_part[0][1].lower(), course_item)
            if duration_full:
                course_item["durationMinFull"] = float(duration_full[0][0])
                self.get_period(duration_full[0][1].lower(), course_item)
            if duration_part:
                if self.teaching_periods[duration_part[0][1].lower()] == course_item["teachingPeriod"]:
                    course_item["durationMinPart"] = float(duration_part[0][0])
                else:
                    course_item["durationMinPart"] = float(duration_part[0][0]) * course_item["teachingPeriod"] \
                                                     / self.teaching_periods[duration_part[0][1].lower()]

        entry = response.xpath("//span[contains(@id, 'entry-requirements-info')]/following-sibling::div[contains("
                               "text(), 'Entry requirements')]/following-sibling::*").getall()
        holder = []
        for item in entry:
            if not re.search("(?<=<[phu])", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            entry = "".join(holder)
            entry = re.sub("\s+", " ", entry, re.M)
            course_item["entryRequirements"] = entry

        rank = response.xpath("//p[contains(span/text(), 'Entry Requirements')]//text()").getall()
        if rank:
            rank = [x.strip() for x in rank]
            rank = "".join(rank)
            rank = re.findall("(?<=Selection Rank \(Guaranteed\)).+?(\d*\.?\d+)", rank, re.M | re.DOTALL)
            if rank:
                try:
                    course_item["guaranteedEntryScore"] = float(rank[0])
                except ValueError:
                    pass

        fee = response.xpath("//p[contains(span/text(), 'Fees')]//text()").getall()
        if fee:
            fee = [x.strip() for x in fee]
            fee = "".join(fee)
            fee = re.search("(?<=\$).*?(\d*),?(\d+)", fee, re.DOTALL | re.M)
            if fee:
                fee = fee.group(1) + fee.group(2)
                try:
                    course_item["domesticFeeAnnual"] = float(fee)
                    get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)
                except ValueError:
                    pass

        course_code = response.xpath("//p[contains(span/text(), 'Program Code')]/text()").get()
        if course_code:
            course_item["courseCode"] = course_code.strip()

        course_item.set_sf_dt(self.degrees, type_delims=["of", "in", "by"], degree_delims=["/", "and", ","])

        course_item["uid"] = course_item["uid"] + "-" + course_item["courseCode"]

        check_int = response.xpath("//span[@class='altis-regular']/text()").get()
        if not check_int or check_int == "Australian students only":
            if response.request.url not in self.banned_urls:
                yield course_item
        else:
            int_link = response.request.url + "/int"

            yield response.follow(int_link, callback=self.international_parse, meta={'item': course_item})

    def international_parse(self, response):
        course_item = response.meta['item']

        cricos = response.xpath("//p[contains(span/text(), 'CRICOS Code')]//text()").getall()
        if cricos:
            cricos = [x.strip() for x in cricos]
            cricos = "".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)

        course_item["internationalApps"] = 1
        course_item["internationalApplyURL"] = response.request.url

        fee = response.xpath("//p[contains(span/text(), 'Fees')]//text()").getall()
        if fee:
            fee = [x.strip() for x in fee]
            fee = "".join(fee)
            fee = re.search("(?<=\$).*?(\d*),?(\d+)", fee, re.DOTALL | re.M)
            if fee:
                fee = fee.group(1) + fee.group(2)
                try:
                    course_item["internationalFeeAnnual"] = float(fee)
                    get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)
                except ValueError:
                    pass

        yield course_item