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


class UodSpiderSpider(scrapy.Spider):
    name = 'uod_spider'
    allowed_domains = ['divinity.edu.au']
    start_urls = ['https://divinity.edu.au/study/courses/']
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

    degrees = {
        "graduate certificate": "7",
        "graduate diploma": "8",
        "master": research_coursework,
        "bachelor": bachelor_honours,
        "doctor": "6",
        "certificate": "4",
        "diploma": "5",
        "associate degree": "1",
        "university foundation studies": "13",
        "non-award": "13",
        "no match": "15"
    }

    campuses = {
        "Australian Lutheran College": "746",
        "Catholic Theological College": "740",
        "Eva Burrows College": "745",
        "Jesuit College of Spirituality": "743",
        "Morling College": "750",
        "St Athanasius College": "748",
        "Pilgrim Theological College": "742",
        "Stirling Theological College": "739",
        "Trinity College Theological School": "747",
        "Whitley College": "741",
        "Yarra Theological Union": "744",
    }

    nums = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10
    }

    def parse(self, response):
        courses = response.xpath("//div[@class='entry-content']//li/a/@href").getall()

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        institution = "University of Divinity"
        uidPrefix = "AU-UOD-"

        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = institution
        course_item["internationalApplyURL"] = response.request.url
        course_item["domesticApplyURL"] = response.request.url

        course_item["courseName"] = response.xpath("//h1[@class='entry-title']/text()").get()
        course_item["uid"] = uidPrefix + re.sub(" ", "-", course_item["courseName"])

        course_item["postNumerals"] = response.xpath("//h5[contains(text(), 'Postnominals')]/following::p/text()").get()
        cricos = response.xpath("//h5[contains(text(), 'CRICOS')]/following::p/text()").get()
        cricos = re.findall("\d{6}[0-9a-zA-Z]", cricos, re.M)
        if len(cricos) > 0:
            course_item["cricosCode"] = cricos[0]
            course_item["internationalApps"] = 1

        study_mode = response.xpath("//h5[contains(text(), 'Study mode')]/following::ul").get()
        study_holder = []
        if study_mode is not None:
            if re.search("online", study_mode, re.I | re.M):
                study_holder.append("Online")
            if re.search("face", study_mode, re.I | re.M):
                study_holder.append("In Person")
            course_item["modeOfStudy"] = "|".join(study_holder)

        overview = response.xpath("//h5[contains(text(), 'What this course is about')]/following::p").get()
        if overview is not None:
            course_item["overview"] = strip_tags(overview, False)

        learn = response.xpath("//*[preceding-sibling::h5/text() = 'Course learning outcomes' and "
                               "following-sibling::h5/text() = 'Follow on study']").getall()
        if len(learn) > 0:
            course_item["whatLearn"] = strip_tags("".join(learn), False)

        entry = response.xpath("//*[preceding-sibling::h5/text() = 'Admission criteria' and "
                               "following-sibling::h5/text() = 'How to apply']").getall()
        if len(entry) > 0:
            course_item["entryRequirements"] = strip_tags("".join(entry), False)

        course_structure = response.xpath("//*[preceding-sibling::h2/text() = 'Course structure' and "
                                          "following-sibling::h2/text() = 'Academic dress']").getall()
        if len(course_structure) > 0:
            course_item["courseStructure"] = strip_tags("".join(course_structure), False)

        admission_date = response.xpath("//*[preceding-sibling::h5/text() = 'Admission dates' and "
                                        "following-sibling::h5/text() = 'Admission criteria']").getall()
        if len(admission_date) > 0:
            admission_date = "".join(admission_date)
            start_holder = []
            for month in self.months:
                if re.search(month, admission_date, re.M):
                    start_holder.append(self.months[month])
            if len(start_holder) > 0:
                course_item["startMonths"] = "|".join(start_holder)

        location = response.xpath("//h5[contains(text(), 'Colleges where it can be studied')]/following::ul").get()
        campus_holder = []
        if location is not None:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.append(self.campuses[campus])
        if len(campus_holder) > 0:
            course_item["campusNID"] = "|".join(set(campus_holder))

        duration = response.xpath("//h5[contains(text(), 'Duration')]/following::p").get()
        duration_holder = []
        for num in self.nums:
            if re.search(num + "\s", duration, re.I):
                duration_holder.append(self.nums[num])
        if len(duration_holder) == 1:
            course_item["durationMinFull"] = duration_holder[0]
        elif len(duration_holder) > 1:
            course_item["durationMinFull"] = min(duration_holder)
            course_item["durationMaxPart"] = max(duration_holder)
        if re.search("semester", duration, re.I):
            course_item["teachingPeriod"] = 2
        elif re.search("year", duration, re.I):
            course_item["teachingPeriod"] = 1

        cost = response.xpath("//h5[contains(text(), 'Cost of study')]/following::p").get()
        cost_holder = []
        if len(cost) > 0:
            fee = re.findall("\$\d+,?\d{3}", cost, re.M)
            if len(fee) > 0:
                for item in fee:
                    cost_holder.append(float(re.sub("\$(\d+),?(\d{3})", r"\1\2", item)))
        print(cost_holder)
        if len(cost_holder) > 0:
            if course_item["teachingPeriod"] == 1:
                course_item["domesticFeeAnnual"] = max(cost_holder)
            elif course_item["teachingPeriod"] == 2:
                course_item["domesticFeeAnnual"] = max(cost_holder) * 2

        course_item.set_sf_dt(self.degrees, ["of", "in"], ["and"])

        yield course_item