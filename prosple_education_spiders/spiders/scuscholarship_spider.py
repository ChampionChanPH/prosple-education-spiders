# -*- coding: utf-8 -*-
# by Christian Anasco

from datetime import datetime
from ..standard_libs import *
from ..scratch_file import strip_tags


class ScuscholarshipSpiderSpider(scrapy.Spider):
    name = 'scuscholarship_spider'
    start_urls = ['https://www.scu.edu.au/scholarships/find-a-scholarship/']
    institution = "Southern Cross University (SCU)"

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

    num = {
        "one": '1',
        "two": '2',
        "three": '3',
        "four": '4',
        "five": '5',
        "six": '6',
        "seven": '7',
        "eight": '8',
        "nine": '9',
        "ten": '10'
    }

    campuses = {
        "Melbourne": "701",
        "Lismore": "695",
        "Gold Coast": "696",
        "Perth": "700",
        "Sydney": "699",
        "Tweed Heads": "698",
        "Coffs Harbour": "697",
        "NMSC": "694"
    }

    def parse(self, response):
        boxes = response.xpath("//tbody/tr")

        for item in boxes:
            url = item.xpath(".//a/@href").get()
            degree = item.xpath("./td[1]").get()
            close_date = item.xpath("./td[last()]/text()").get()
            campus = item.xpath("./td[2]").get()
            if url:
                yield response.follow(url, callback=self.scholarship_parse, meta={'close_date': close_date,
                                                                                  'campus': campus, 'degree': degree})

    def scholarship_parse(self, response):
        scholarship_item = Scholarship()

        scholarship_item["source_url"] = response.request.url
        scholarship_item["published"] = 1
        scholarship_item["provider_name"] = self.institution

        name = response.xpath("//h1/text()").get()
        if name:
            scholarship_item["name"] = re.sub("\s+", " ", name.strip())

        overview = response.xpath("//h1/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(overview):
            if re.search("^<div", item):
                pass
            elif (index == 0 or re.search("^<p", item)) and not re.search("Application process", item):
                holder.append(item)
            elif index != 0 and not re.search("^<p", item):
                break
            elif re.search("Application process", item):
                break
        if holder:
            scholarship_item.set_summary(' '.join([strip_tags(x) for x in holder]))
            scholarship_item['overview'] = strip_tags(''.join(holder), False)

        degree = response.meta['degree']
        if re.search('Undergraduate', degree, re.I):
            scholarship_item['canonical_group'] = 'The Uni Guide'
        else:
            scholarship_item['canonical_group'] = 'PostgradAustralia'

        eligibility = response.xpath("//*[self::h3 or self::h2][text()='Non eligibility' or text("
                                     ")='Eligibility' or text()='Eligibility criteria']/following-sibling::*").getall()
        holder = []
        for item in eligibility:
            if re.search('^<ul', item) or re.search('^<ol', item):
                holder.append(item)
                break
            else:
                holder.append(item)
        if holder:
            scholarship_item['eligibility'] = strip_tags(''.join(holder), False)

        value = response.xpath("//*[text()='Value' or text()='Amount' or text()='ValuE' or */text("
                               ")='Value']/following-sibling::*").get()
        if value:
            value = re.findall("\$(\d*),?(\d+)", value)
            value = [float(''.join(x)) for x in value]
            if value:
                scholarship_item['total_value'] = max(value)

        application_process = response.xpath("//*[contains(text(), 'Application process') or contains(*/text(), "
                                             "'Application process')]/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(application_process):
            if index == 0 or re.search("^<p", item) or re.search("^<ul", item) or re.search("^<ol", item):
                holder.append(item)
            else:
                break
        if holder:
            scholarship_item['app_process'] = strip_tags(''.join(holder), False)

        criteria = response.xpath("//*[contains(text(), 'Selection criteria') or contains(*/text(), 'Selection "
                                  "criteria')]/following-sibling::*").getall()
        holder = []
        for index, item in enumerate(criteria):
            if index == 0 or re.search("^<p", item) or re.search("^<ul", item) or re.search("^<ol", item):
                holder.append(item)
            elif re.search("#top", item):
                pass
            else:
                break
        if holder:
            scholarship_item['criteria'] = strip_tags(''.join(holder), False)

        location = response.meta['campus']
        campus_holder = set()
        study_holder = set()
        if location:
            for campus in self.campuses:
                if re.search(campus, location, re.I):
                    campus_holder.add(self.campuses[campus])
                if re.search('online', location, re.I):
                    study_holder.add('Online')
            if len(campus_holder) == 1 and 'Online' not in study_holder:
                study_holder.add('In person')
            if len(campus_holder) > 1:
                study_holder.add('In person')
            if campus_holder:
                scholarship_item['campus_names'] = '|'.join(campus_holder)
            if study_holder:
                scholarship_item['study_mode'] = '|'.join(study_holder)
        if "699" in campus_holder:
            scholarship_item['time_zone'] = 'Sydney'
        elif "701" in campus_holder:
            scholarship_item['time_zone'] = 'Melbourne'
        elif "700" in campus_holder:
            scholarship_item['time_zone'] = 'Perth'
        else:
            scholarship_item['time_zone'] = 'Sydney'

        close_date = response.meta['close_date']
        if close_date:
            close_date = close_date.strip()
            if not re.search('n/a', close_date, re.I) and not re.search('tbc', close_date, re.I):
                for month in self.months:
                    close_date = re.sub(month, self.months[month], close_date)
                close_date = datetime.strptime(close_date, '%d %m %Y')
                scholarship_item['closes'] = close_date.strftime("%m/%d/%Y") + " 00:00:00"

        count = response.xpath("//*[contains(text(), 'Number available') or contains(*/text(), 'Number "
                               "available')]/following-sibling::*/text()").get()
        if count:
            scholarship_item['count_description'] = count.strip()

        duration = response.xpath("//*[contains(text(), 'Duration')]/following-sibling::*/text()").get()
        if not duration:
            duration = response.xpath(
                "//*[text()='Value' or text()='Amount' or text()='ValuE']/following-sibling::*").get()
        if duration:
            for num in self.num:
                duration = re.sub(num, self.num[num], duration)
            duration_full = re.findall("(\d*\.?\d+)(?=(\s)(year|month|semester|trimester|quarter|week|day)(s?))", duration,
                                       re.I | re.M | re.DOTALL)
            if duration_full:
                scholarship_item['length_support'] = ''.join(duration_full[0])
            if 'length_support' not in scholarship_item and re.search('one.off.payment', duration, re.I | re.M):
                scholarship_item['length_support'] = 'One-off payment'

        yield scholarship_item
