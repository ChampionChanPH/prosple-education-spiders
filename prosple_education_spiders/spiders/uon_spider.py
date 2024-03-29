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


class UonSpider(scrapy.Spider):
    name = 'uon_spider'
    allowed_domains = ['www.newcastle.edu.au', 'newcastle.edu.au']
    start_urls = ['https://www.newcastle.edu.au/degrees']
    banned_urls = ['degrees/master-engineering-management',
                   'degrees/graduate-certificate-financial-planning',
                   'degrees/graduate-certificate-integrated-science-technology-engineering-mathematics']
    institution = "University of Newcastle"
    uidPrefix = "AU-UON-"

    campuses = {
        "Online": "46712",
        "UON Singapore": "776",
        "Sydney CBD": "775",
        "Newcastle City": "35878",
        "Newcastle": "772",
        "Central Coast": "773"
    }

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "executive master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "undergraduate certificate": "4",
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
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }

    def get_period(self, string_to_use, course_item):
        for item in self.teaching_periods:
            if re.search(item, string_to_use):
                course_item["teachingPeriod"] = self.teaching_periods[item]

    def parse(self, response):
        boxes = response.xpath("//table[@class='handbook-degree-listing']/tbody/tr[@data-degreeid]")

        for item in boxes:
            url = item.xpath(".//a[@class='degree-link']/@href").get()
            intake = item.xpath(".//td[@class='no-further-intake']").get()
            atar = item.xpath(".//td[@class='degree-atar']").get()
            if not intake:
                if url not in self.banned_urls:
                    if atar:
                        yield response.follow(url, callback=self.course_parse, meta={'atar': atar})
                    else:
                        yield response.follow(url, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        course_name = response.xpath("//h1[@class='page-header-title']//text()").getall()
        if not course_name:
            course_name = response.xpath("//h1//text()").getall()
        course_name = [x.strip() for x in course_name if x != '']
        course_name = ' '.join(course_name)
        if course_name:
            course_item.set_course_name(course_name.strip(), self.uidPrefix)

        overview = response.xpath("//h3[@id='description']/following-sibling::*").getall()
        if not overview:
            overview = response.xpath("//div[@class='grid-block']/*").getall()
        if not overview:
            overview = response.xpath("//h1/following-sibling::*").getall()
        holder = []
        for item in overview:
            if not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M):
                break
            elif strip_tags(item).strip() != '':
                item = re.sub("<img.*?>", "", item, re.DOTALL)
                holder.append(item)
        if len(holder) == 1:
            course_item.set_summary(strip_tags(holder[0]))
            course_item["overview"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)
        if len(holder) > 1:
            course_item.set_summary(strip_tags(holder[0] + holder[1]))
            course_item["overview"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        location = response.xpath("//nav[@class='fast-fact-toggle']//text()").getall()
        if location:
            location = ", ".join(location)
            campus_holder = []
            for campus in self.campuses:
                if campus == "Newcastle":
                    if re.search("Newcastle(?!\sCity)", location, re.I | re.M):
                        campus_holder.append(self.campuses[campus])
                elif re.search(campus, location, re.I | re.M):
                    campus_holder.append(self.campuses[campus])
            if campus_holder:
                course_item["campusNID"] = "|".join(campus_holder)

        career = response.xpath("//h2[contains(text(), 'Career opportunities')]/following-sibling::*").getall()
        holder = []
        for item in career:
            if (not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M)) or \
                    re.search("class=", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["careerPathways"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        duration = response.xpath("//*[contains(text(), 'Duration')]/following-sibling::*").get()
        if duration:
            duration_full = re.findall("(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day)s?\sfull.time)",
                                       duration, re.I | re.M | re.DOTALL)
            duration_part = re.findall(
                "(?<=part.time.equivalent.up.to.)(\d*\.?\d+)(?=\s(year|month|semester|trimester|quarter|week|day))",
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

        study = response.xpath("//*[contains(text(), 'Mode of delivery')]/following-sibling::*").getall()
        if study:
            study = "".join(study)
            holder = []
            if re.search("face", study, re.I | re.M):
                holder.append("In Person")
            if re.search("online", study, re.I | re.M):
                holder.append("Online")
            if holder:
                course_item["modeOfStudy"] = "|".join(holder)

        intake = response.xpath("//*[contains(text(), 'Start dates')]/following-sibling::*").get()
        if intake:
            start_holder = []
            for item in self.months:
                if re.search(item, intake, re.M):
                    start_holder.append(self.months[item])
            if start_holder:
                course_item["startMonths"] = "|".join(start_holder)

        course_code = response.xpath("//div[@class='uon-code']/div").get()
        if not course_code:
            course_code = response.xpath("//*[contains(text(), 'Program Code')]/following-sibling::*/text()").get()
        if course_code:
            course_code = re.findall("\d+", course_code, re.M)
            if course_code:
                course_item["courseCode"] = ", ".join(course_code)

        cricos = response.xpath("//div[contains(@class, 'cricos-code')]//text()").getall()
        if not cricos:
            cricos = response.xpath("//*[contains(text(), 'CRICOS Code')]/following-sibling::*//text()").getall()
        if cricos:
            cricos = " ".join(cricos)
            cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
            if cricos:
                course_item["cricosCode"] = ", ".join(cricos)
                course_item["internationalApps"] = 1
                course_item["internationalApplyURL"] = response.request.url

        learn = response.xpath("//*[contains(@id, 'what-you-will-study')]/*[contains(@class, 'clearfix')]/*/*").getall()
        if not learn:
            learn = response.xpath("//div[@id='section-program-learning-outcomes']/*").getall()
        holder = []
        for item in learn:
            if not re.search("^<p", item, re.M) and not re.search("^<ul", item, re.M):
                break
            else:
                holder.append(item)
        if holder:
            course_item["whatLearn"] = strip_tags("".join(holder), remove_all_tags=False, remove_hyperlinks=True)

        dom_fee = response.xpath("//span[contains(@class, 'icons8-us-dollar')]/following-sibling::*["
                                 "@data-region='australian']").get()
        if dom_fee:
            dom_fee = re.findall("AUD\s(\d*),?(\d+)(\.\d\d)?", dom_fee, re.M)
            dom_fee = [float(''.join(x)) for x in dom_fee]
            if dom_fee:
                course_item["domesticFeeAnnual"] = max(dom_fee)
                get_total("domesticFeeAnnual", "domesticFeeTotal", course_item)

        int_fee = response.xpath("//span[contains(@class, 'icons8-us-dollar')]/following-sibling::*["
                                 "@data-region='international']").get()
        if int_fee:
            int_fee = re.findall("AUD\s(\d*),?(\d+)(\.\d\d)?", int_fee, re.M)
            int_fee = [float(''.join(x)) for x in int_fee]
            if int_fee:
                course_item["internationalFeeAnnual"] = max(int_fee)
                get_total("internationalFeeAnnual", "internationalFeeTotal", course_item)

        if 'atar' in response.meta:
            atar = response.meta['atar']
            if atar:
                atar = re.findall('(\d+)(\.\d{2})?', atar)
                if atar:
                    course_item['guaranteedEntryScore'] = float(''.join(atar[0]))

        if 'uid' in course_item and 'courseCode' in course_item:
            course_item["uid"] = course_item["uid"] + '-' + course_item['courseCode']

        if "courseName" in course_item:
            if course_item['courseName'].lower() not in ['phd and research masters', 'yapug', 'newstep', 'music',
                                                         'fine art', 'creative and performing arts']:
                course_item.set_sf_dt(self.degrees, degree_delims=['and', '/'], type_delims=['of', 'in', 'by'])
                if course_item['courseName'] == 'Juris Doctor / Graduate Diploma in Legal Practice':
                    course_item['rawStudyfield'] = ['law', 'legal practice']
                    course_item['specificStudyField'] = 'Law / Legal Practice'
                if 'degreeType' in course_item:
                    if course_item['degreeType'] == '3':
                        course_item['group'] = 3
                        course_item['canonicalGroup'] = 'The Uni Guide'
                yield course_item