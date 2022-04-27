# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


class EcuscholarshipSpiderSpider(scrapy.Spider):
    name = 'ecuscholarship_spider'
    handle_httpstatus_list = [410]
    start_urls = ['https://www.ecu.edu.au/scholarships/offers']
    institution = "Edith Cowan University (ECU)"
    uidPrefix = 'AU-ECU-'

    def parse(self, response):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'}

        scholarships = response.xpath(
            "//div[@class='span7']//h3/a/@href").getall()

        for scholarship in scholarships:
            yield response.follow(scholarship, callback=self.scholarship_parse, headers=headers, meta={"handle_httpstatus_list": [410]})

    def scholarship_parse(self, response):
        scholarship_item = Scholarship()

        scholarship_item["source_url"] = response.request.url
        scholarship_item["published"] = 1
        scholarship_item["provider_name"] = self.institution

        scholarship_name = response.xpath(
            "//h2[@class='page-title']/text()").get()
        if scholarship_name:
            scholarship_item.set_scholarship_name(
                scholarship_name.strip(), self.uidPrefix)

        overview = response.xpath(
            "//*[contains(@class, 'scholarshipsOverview__summary')]").getall()
        if overview:
            summary = [strip_tags(x) for x in overview]
            scholarship_item.set_summary(' '.join(summary))
            scholarship_item['overview'] = strip_tags(
                ''.join(overview), remove_all_tags=False, remove_hyperlinks=True)

        scholarship_item["time_zone"] = "Australia/Sydney"
        scholarship_item["eligible"] = self.institution

        degree_type = response.css(
            "div.tags span.labelHighlight--blueAlt").getall()
        if degree_type:
            degree_type = ''.join(degree_type)
            if re.search("Undergraduate", degree_type) and re.search("Postgraduate", degree_type):
                scholarship_item['canonical_group'] = 'The Uni Guide'
                scholarship_item['group'] = 3
                scholarship_item[
                    'degree_types'] = "Associate Degree|Bachelor|Certificate|Diploma|Professional Certificate|Bachelor (Honours)|Doctorate (PhD)|Graduate Certificate|Graduate Diploma|Juris Doctor|Masters (Coursework)|Masters (Research)"
            elif re.search("Undergraduate", degree_type):
                scholarship_item['canonical_group'] = 'The Uni Guide'
                scholarship_item['group'] = 3
                scholarship_item['degree_types'] = "Associate Degree|Bachelor|Certificate|Diploma|Professional Certificate"
            elif re.search("Postgraduate", degree_type):
                scholarship_item['canonical_group'] = 'PostgradAustralia'
                scholarship_item['group'] = 4
                scholarship_item['degree_types'] = "Bachelor (Honours)|Doctorate (PhD)|Graduate Certificate|Graduate Diploma|Juris Doctor|Masters (Coursework)|Masters (Research)"

        open = response.css("div.dates span.labelHighlight--greenAlt").get()
        if open:
            application_open = re.findall("(\d{1,2})-(\d{2})-20(\d{2})", open)
            scholarship_item["opens"] = '/'.join(
                application_open[0]) + " 00:00"

        close = response.css("div.dates span.labelHighlight--redAlt").get()
        if close:
            application_close = re.findall(
                "(\d{1,2})-(\d{2})-20(\d{2})", close)
            scholarship_item["closes"] = '/'.join(
                application_close[0]) + " 00:00"

        scholarship_item["apply_url"] = response.request.url

        eligibility = response.xpath(
            "//h3[text()='Eligibility guidelines']/following-sibling::*").getall()
        holder = []
        for item in eligibility:
            if re.search("^<(p|o|u)", item):
                holder.append(item)
            else:
                break
        if holder:
            scholarship_item['eligibility'] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        apply = response.xpath(
            "//h3[text()='How to apply']/following-sibling::*").getall()
        holder = []
        for item in apply:
            if re.search("^<(p|o|u)", item):
                holder.append(item)
            else:
                break
        if holder:
            scholarship_item['app_process'] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)

        conditions = response.xpath(
            "//h3[text()='Terms and conditions']/following-sibling::*").getall()
        holder = []
        for item in conditions:
            if re.search("^<(p|o|u)", item):
                holder.append(item)
            else:
                break
        if holder:
            scholarship_item['retention'] = strip_tags(
                ''.join(holder), remove_all_tags=False, remove_hyperlinks=True)
