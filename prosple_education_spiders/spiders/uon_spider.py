import scrapy
import re
from ..items import Course
from datetime import date

uon_campus = ['Newcastle', 'Newcastle City', 'UON Singapore', 'Central Coast', 'Sydney CBD']
months = {'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April', 'May': 'May', 'Jun': 'June',
          'Jul': 'July', 'Aug': 'August', 'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'}

class UonSpider(scrapy.Spider):
    name = 'uon_spider'
    allowed_domains = ['www.newcastle.edu.au']
    start_urls = ['http://www.newcastle.edu.au/degrees/']

    def strip_tags(sentence, remove_all_tags=True):
        if remove_all_tags:
            strip = re.sub("</?.*?>", "", sentence)
            return strip
        else:
            strip = re.sub("(?<=<)(h[1-6]).*?(?=>)", "strong", strip)
            strip = re.sub("(?<=</)(h[1-6]).*?(?=>)", "strong", strip)
            return strip

    def parse(self, response):
        courses = response.css("div.col.w75").css("a.degree-link::attr(href)").getall()
        courses = set(courses)
        courses = [i for i in courses if not (bool(re.search("-20", i)))]

        for course in courses:
            yield response.follow(course, callback=self.course_parse)

    def course_parse(self, response):
        if response.css('div.discontinued-content').get() is not None:
            return

        if response.css("h1.page-header-title").get() is None:
            return

        course_item = Course()
        course_item["lastUpdate"] = date.today().strftime("%m/%d/%y")
        course_item["sourceURL"] = response.request.url

        course_name = response.css("h1.page-header-title").get()
        course_name = course_name.split(' ')
        course_name = [i for i in course_name if i != '']
        course_name = ' '.join(course_name)
        course_item['courseName'] = UonSpider.strip_tags(course_name).strip()

        course_campus = response.css("div.fast-facts-content").css("em::text").getall()
        campus_list = []
        for campus in course_campus:
            global uon_campus
            if (campus in uon_campus) and (campus not in campus_list):
                campus_list.append(campus)
        if len(campus_list) > 0:
            course_item['campusNID'] = ', '.join(campus_list)

        career = response.css('div#career-opportunities.about-tab').get()
        if career is not None:
            course_item['careerPathways'] = career

        duration = response.css("div.fast-facts-content").get()
        if duration is not None:
            course_item['durationRaw'] = UonSpider.strip_tags(duration)

            get_minfull = re.findall('[0-9]?\.?[0-9]+(?=.year.+?full.time)', duration)
            if len(get_minfull) > 0:
                course_item['durationMinFull'] = float(get_minfull[0])

            get_minpart = re.findall('(?<=part.time.equivalent.up.to.)[0-9]+', duration)
            if len(get_minpart) > 0:
                course_item['durationMinPart'] = float(get_minpart[0])

        study_mode = response.css(".icons8-classroom~ p").css("::text").get()
        if study_mode is not None:
            holder = []
            if re.search('face', study_mode, re.IGNORECASE):
                holder.append('In Person')
            if re.search('online', study_mode, re.IGNORECASE):
                holder.append('Online')
            course_item['modeOfStudy'] = '|'.join(holder)

        get_months = re.compile('(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)')
        if response.css('.icons8-calendar~ ul').get() is not None:
            start_months = get_months.findall(response.css('.icons8-calendar~ ul').get())
            start_months = {i for i in start_months}
            global months
            start_months = [months[i] for i in start_months]
            course_item['startMonths'] = ", ".join(start_months)

        course_item['courseCode'] = response.css('div.uon-code').css('strong::text').get()
        cricos = response.css('div.cricos-code').css('a::text').get()
        if cricos is not None:
            course_item['cricosCode'] = cricos.zfill(7)

        # Check format used in page
        if response.css('div#degree-details').get() is None:
            overview = response.css('div.grid-block').get()
        else:
            overview = re.findall('(?<=Description</h3>).+?(?=<hr>)', response.css('div#degree-details').get(), re.DOTALL)
            if len(overview) > 0:
                overview = overview[0]
            else:
                overview = ''
        course_item['overview'] = overview

        fees = response.css('.icons8-us-dollar~ p').getall()
        if len(fees) > 0:
            int_fee = re.findall('([0-9]+)[.,]?([0-9]{3})', fees[-1])
            int_fee_holder = []
            if len(int_fee) > 0:
                int_fee = int_fee[0][0] + int_fee[0][1]
                int_fee_holder.append(int_fee)
            fee_year = re.findall('20[0-9]{2}', fees[-1])
            if len(fee_year) > 0:
                int_fee_holder.append(fee_year[0])
            course_item['internationalFeeAnnual'] = ", ".join(int_fee_holder)

        atar = response.css('div.entrance-rank').get()
        lowest_atar = []
        median_atar = []
        if atar is not None:
            lowest_atar = re.findall('Selection\sRank<.*?>([0-9]+.[0-9]+)', atar)
            median_atar = re.findall('<strong>([0-9]+.[0-9]+)<.*?>\s+\(Median', atar)
        if len(lowest_atar) > 0:
            course_item['lowestScore'] = float(lowest_atar[0])
        if len(median_atar) > 0:
            course_item['medianScore'] = float(median_atar[0])

        yield course_item