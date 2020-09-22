# by: Johnel Bacani
# 09-22-20
from ..standard_libs import *


class CourseraSpider(scrapy.Spider):
    name = 'coursera'
    # allowed_domains = ['https://www.coursera.org/']
    start_urls = [
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.11842473122&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fuva-darden-managerial-accounting",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.10188598426&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fuva-darden-financial-accounting",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.4036978638&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Ffinancial-accounting-basics",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.2294900595&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Fspecializations%2Faccounting-fundamentals",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.1745054388&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Fspecializations%2Finvestment-management",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.10508402412&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Ffinancial-markets-global",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.5329718105&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fmoney-banking",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.9931479992&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Ffood-and-health",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.10360580176&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fscience-exercise",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.14021095881&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fweight-management-beyond-balancing-calories",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.10188598634&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fuva-darden-project-management",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.14526731426&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fmanagement-accounting",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.12375824992&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fmanagement-fundamentals-healthcare-administrators",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.11919003996&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Femerging-technologies-lifelong-learning",
        "https://click.linksynergy.com/link?id=ZDcWIaB8nkQ&offerid=759505.13318814098&type=2&murl=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fiot-wireless-cloud-computing"
    ]

    uidPrefix = "COURSERA-"

    def parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        # course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url
        course_item["internationalApps"] = 1
        course_item["modeOfStudy"] = "Online"
        course_item["startMonths"] = "01|02|03|04|05|06|07|08|09|10|11|12"


        course_item["courseLevel"] = "1"
        course_item["degreeType"] = "16"
        course_item["group"] = 3
        course_item["canonicalGroup"] = "The Uni Guide"

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)
            course_item["studyField"] = name

        overview = response.css(".description p::text").get()
        if overview:
            course_item["overview"] = overview

            course_item.set_summary(overview)

        partner = response.css(".rc-Partner h4::text").get()
        if partner:
            course_item["institution"] = partner

        weekheadings = response.css(".SyllabusModule h2::text").getall()
        weekdetails = response.css(".SyllabusModule p::text").getall()
        if weekheadings and weekdetails and len(weekdetails) == len(weekheadings):
            weeks = range(len(weekheadings))
            structure = ["<strong>Week "+str(x+1)+"</strong>\n<strong>"+y+"</strong>\n"+z for x in weeks for y in weekheadings for z in weekdetails]
            course_item["courseStructure"] = "\n\n".join(structure)
            course_item["teachingPeriod"] = 52
            course_item["durationMinFull"] = len(weeks)

        yield course_item
