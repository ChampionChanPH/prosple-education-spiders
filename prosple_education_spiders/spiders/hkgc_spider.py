# -*- coding: utf-8 -*-
# by Christian Anasco
# scraper to get internships and graduate jobs from HK GradConnection

import requests
import csv
import re
from prosple_education_spiders.taxonomy import special_chars
from prosple_education_spiders.scratch_file import strip_tags

jobType = {
    'Graduate Jobs': 'Graduate Job',
    'Internships': 'Internship',
}


def set_summary(text):
    max_characters = 300
    summary = None

    text = re.split('(?<=[.?!])\s', text)
    if len(text) == 1:
        if len(text[0]) < max_characters:
            summary = text[0]
        else:
            cut_summary = text[0][:max_characters + 1]
            last_space = cut_summary.rindex(' ')
            summary = cut_summary[:last_space] + '...'
    if len(text) > 1:
        temp_holder = []
        char_count = 0
        for index, item in enumerate(text):
            if index == 0 and len(item) > max_characters:
                cut_summary = text[0][:max_characters + 1]
                last_space = cut_summary.rindex(' ')
                summary = cut_summary[:last_space] + '...'
                temp_holder.append(summary)
                break
            elif char_count + len(item) > max_characters:
                break
            else:
                char_count += len(item) + 1
                temp_holder.append(item)
        summary = ' '.join(temp_holder).strip()

    return summary


def clean_data(text):
    for characters in list(special_chars.keys()):
        text = text.replace(characters, special_chars[characters])
    return text


def format_date(text):
    date = re.findall('(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)\+(\d+:\d+)', text)
    if date:
        YY, MM, DD, hh, mm, ss, timezone = date[0]
        am_pm = "AM"
        if int(hh) > 12:
            hh = str(int(hh) - 12).zfill(2)
            am_pm = "PM"
        return f"{MM}/{DD}/{YY} {hh}:{mm}:{ss} {am_pm}"
    return text


class HKGradConnection:
    def __init__(self, term, offset):
        self.term = term
        self.offset = offset

    def set_url(self):
        return f"https://hk.gradconnection.com/api/campaigngroups/?job_type={self.term}&offset={str(self.offset)}" \
               f"&limit=20&ordering=&page=1"

    def get_data(self):
        result = requests.get(self.set_url())
        return result.json()

    def parse_data(self):
        data = self.get_data()

        employer_list = set()
        group = 56
        canonical_group = 'GradHongKong'

        for employer in data:
            employer_name = clean_data(employer['customer_organization']['name'])
            employer_slug = employer['customer_organization']['slug']
            employer_description = clean_data(employer['customer_organization']['description'])
            employer_url = 'https://hk.gradconnection.com/employers/' + employer_slug
            employer_discipline = employer['display_disciplines']
            employer_location = employer['customer_organization']['country']['name']
            if employer_discipline:
                employer_discipline = '|'.join(employer_discipline)
                
            opportunity_type = set()

            for campaign in employer['campaigns']:
                job_title = clean_data(campaign['title'])
                job_slug = campaign['slug']
                job_description = clean_data(campaign['description'])
                job_discipline = campaign['display_disciplines']
                if job_discipline:
                    job_discipline = '|'.join(job_discipline)
                job_start = format_date(campaign['interval']['start'])
                job_end = format_date(campaign['interval']['end'])
                job_type = campaign['job_type']
                if job_type == 'Graduate Jobs':
                    job_type = jobType['Graduate Jobs']
                    opportunity_type.add(jobType['Graduate Jobs'])
                if job_type == 'Internships':
                    job_type = jobType['Internships']
                    opportunity_type.add(jobType['Internships'])
                job_url = employer_url + '/jobs/' + job_slug + '/'
                job_email = campaign['target_email']
                job_location = campaign['locations']
                job_timezone = ''
                if 'Hong Kong' in job_location:
                    job_timezone = 'Asia/Hong Kong'
                    job_location = 'Hong Kong'
                if 'Shanghai' in job_location:
                    job_timezone = 'Asia/Shanghai'
                    job_location = 'China'

                job_details = [
                    group,
                    canonical_group,
                    job_title,
                    job_timezone,
                    employer_name,
                    job_type,
                    job_description,
                    set_summary(strip_tags(job_description)),
                    job_url,
                    job_location,
                    job_start,
                    job_end,
                    job_discipline,
                    job_email,
                ]

                with open('hkgc_jobs.csv', 'a', newline='') as f:
                    f = csv.writer(f)
                    f.writerow(job_details)

                employer_type = '|'.join(opportunity_type)
                employer_logo = 'Logo-employer-default-240x240-2019.png'
                employer_banner = 'Employer_Banner_890x320_2021.jpg'

                employer_details = [
                    group,
                    canonical_group,
                    employer_name,
                    employer_name,
                    employer_description,
                    employer_description,
                    set_summary(strip_tags(employer_description)),
                    set_summary(strip_tags(employer_description)),
                    set_summary(strip_tags(employer_description)),
                    employer_url,
                    employer_location,
                    employer_discipline,
                    employer_type,
                    employer_logo,
                    employer_banner,
                ]

                if employer_name not in employer_list:
                    employer_list.add(employer_name)
                    with open('hkgc_employers.csv', 'a', newline='') as f:
                        f = csv.writer(f)
                        f.writerow([employer_details[x] for x in range(len(employer_details))])

        return data


with open('hkgc_employers.csv', 'w', newline='') as file:
    fieldnames = [
        'group',
        'Canonical Group',
        'Employer name',
        'Advertiser name',
        'Employer overview - Student Audience (body)',
        'Employer overview - General Audience (body)',
        'Employer overview - Student Audience (summary)',
        'Employer overview - General Audience (summary)',
        'Summary',
        'Employer Profile Link',
        'Locations',
        'Hiring from',
        'Opportunity types',
        'Logo',
        'Banner',
        'Industry Sectors',
    ]
    file = csv.writer(file)
    file.writerow(fieldnames)

with open('hkgc_jobs.csv', 'w', newline='') as file:
    fieldnames = [
        'group',
        'Canonical Group',
        'Opportunity name',
        'Time zone',
        'Employer name',
        'Opportunity types',
        'Overview: Text',
        'Overview: Summary',
        'Link to applications page',
        'Locations',
        'APPLICATIONS OPEN DATE',
        'APPLICATIONS CLOSE DATE',
        'Study field',
        'Apply by form email',
        'Industry Sectors',
    ]
    file = csv.writer(file)
    file.writerow(fieldnames)

keywords = ['internships', 'graduate-jobs']
for keyword in keywords:
    __offset = 0
    while True:
        scraper = HKGradConnection(keyword, __offset)
        scraper = scraper.parse_data()
        if not scraper:
            break
        else:
            __offset += 20
