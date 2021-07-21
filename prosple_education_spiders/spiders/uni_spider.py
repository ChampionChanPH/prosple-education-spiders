 # by: Johnel Bacani
# started: October 5, 2020
# updated: July 21, 2021 by Christian Anasco

from ..standard_libs import *
from ..scratch_file import strip_tags

class UniSpiderSpider(scrapy.Spider):
    name = 'uni_spider'
    allowed_domains = ['www.unitec.ac.nz']
    start_urls = ['https://www.unitec.ac.nz/']
    http_user = 'b4a56de85d954e9b924ec0e0b7696641'
    blacklist_urls = []
    scraped_urls = []
    superlist_urls = []

    institution = "Unitec Institute of Technology"
    uidPrefix = "AU-UNI-"

    holder = []

    campuses = {
        'Waitākere': "55575",
        'North Shore': "55576",
        'Mt Albert': "55577"
    }

    degrees = {
        # "graduate certificate": "7",
        "postgraduate diploma": "8",
        "master": "11",
        "new zealand diploma": "5",
        # "bachelor": ,
        # "doctor": "6",
        "new zealand certificate": "4",
        # "certificate i": "4",
        # "certificate ii": "4",
        # "certificate iii": "4",
        # "certificate iv": "4",
        # "advanced diploma": "5",
        # "diploma": "5",
        # "associate degree": "1",
        # "non-award": "13",
        # "no match": "15"
    }
    # all_terms = get_terms()
    # word_list = ['financial planning','commerce (financial planning)','stockbroking and financial advising','financial technologies','financial technologies (advanced)','accounting with a major in accounting and financial planning','business with a major in financial planning','business with a major in accounting and financial planning','financial planning online delivery','professional accounting /  master of financial planning','business (professional) with a major in financial planning','financial services','business (financial planning)','business (honours) (financial planning)','financial mathematics','financial analysis','financial technology management','applied financial technology and blockchain','fraud and financial crime','decision risk and financial sciences','financial technology','finance (financial planning)','financial management','financial engineering','financial management (professional)','financial markets analysis','demystifying the numbers – understanding financial concepts in healthcare','financial counselling','science (actuarial and financial science)']
    def parse(self, response):
        course_cards = response.css(".progrow:not(#progrow):not(.overview)")
        for card in course_cards:
            course = re.findall("'(.*?)'", card.css("div::attr(onclick)").get())[0]
            if course not in self.blacklist_urls and course not in self.scraped_urls:
                if (len(self.superlist_urls) != 0 and course in self.superlist_urls) or len(self.superlist_urls) == 0:
                    self.scraped_urls.append(course)
                    yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        course_item = Course()

        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url
        course_item["published"] = 1
        course_item["institution"] = self.institution
        course_item["domesticApplyURL"] = response.request.url

        name = response.css("h1::text").get()
        if name:
            course_item.set_course_name(name, self.uidPrefix)

        course_item.set_sf_dt(self.degrees)
        # update_matches(course_item, self.all_terms)
        #Override canon group
        course_item["canonicalGroup"] = "GradNewZealand"
        course_item["group"] = 2

        # for term in course_item["rawStudyfield"]:
        #     # if "financial" in term:
        #     print(term)
        #     print(process.extractOne(term, self.word_list, scorer=fuzz.token_sort_ratio))

        campus = response.css("dl.programme-campus dd::text").getall()
        if campus:
            campus = " ".join(campus).split(",")
            campus = [cleanspace(x) for x in campus if cleanspace(x) != ""]
            holder = []
            for i in campus:
                if i in list(self.campuses.keys()):
                    holder.append(self.campuses[i])
                else:
                    course_item.add_flag("campusNID", "New campus found: "+i)
            course_item["campusNID"] = "|".join(holder)

        dates = response.css("dl.programme-dates dd::text").get()
        if dates:
            months = convert_months(dates.replace(",", "").split(" "))
            course_item["startMonths"] = "|".join(months)

        duration = response.css("dl.programme-duration dd::text").get()

        # if duration:
        #     print(duration)

        summary = response.css(".page-detail__column p::text").get()
        if summary:
            course_item["overviewSummary"] = summary

        overview = response.css("div.overview-content").get()
        if overview:
            overview = overview.replace("<div>", "").replace("</div>", "")
            course_item["overview"] = strip_tags(overview, remove_all_tags=False, remove_hyperlinks=True)

        careers = response.xpath("//ul[preceding-sibling::h3/text()='Career Options']/li/text()").getall()
        if careers:
            careers = "\n".join(["- "+x for x in careers])
            course_item["careerPathways"] = strip_tags(careers, remove_all_tags=False, remove_hyperlinks=True)

        fees = response.xpath("//div[preceding-sibling::h3/text()='Annual Tuition Fees']/span").getall()
        if fees:
            for item in fees:
                if "Domestic" in item:
                    field = "domesticFeeAnnual"

                elif "International" in item:
                    field = "internationalFeeAnnual"

                else:
                    course_item.add_flag("fees", "Could not find fee: "+item)

                fee = re.findall("\$([\d,\.]+)", item)
                if fee:
                    course_item[field] = fee[0].replace(",", "")

        admission = response.css("section#admission div").get()
        if admission:
            admission = admission.replace("<div>", "").replace("</div>", "")
            course_item["entryRequirements"] = strip_tags(admission, remove_all_tags=False, remove_hyperlinks=True)

        # if "flag" in course_item:
        yield course_item
