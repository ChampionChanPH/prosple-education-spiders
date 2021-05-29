# -*- coding: utf-8 -*-
# by Christian Anasco
# scraper to get internships and graduate jobs from HK GradConnection

import requests
import csv
from ..taxonomy import special_chars

jobType = {
    'Graduate Jobs': 'Graduate Job',
    'Internships': 'Internship',
}


class HKGradConnection:
    def __init__(self, term, offset):
        self.term = term
        self.offset = offset

    def set_url(self):
        return 'https://hk.gradconnection.com/api/campaigngroups/?job_type=' + self.term + '&offset='\
               + str(self.offset) + '&limit=20&ordering=&page=1'

    def get_data(self):
        r = requests.get(self.set_url())
        return r.json()

    def clean_data(self, text):
        for characters in list(special_chars.keys()):
            text = text.replace(characters, special_chars[characters])
        return text

    def parse_data(self):
        data = self.get_data()

        for item in data:
            employer_name = self.clean_data(item['customer_organization']['name'])
            employer_slug = item['customer_organization']['slug']
            employer_url = 'https://hk.gradconnection.com/employers/' + employer_slug

            for campaign in item['campaigns']:
                job_title = self.clean_data(campaign['title'])
                job_slug = campaign['slug']
                job_description = self.clean_data(campaign['description'])
                job_start = campaign['interval']['start']
                job_end = campaign['interval']['end']
                job_type = campaign['job_type']
                if job_type == 'Graduate Jobs':
                    job_type = jobType['Graduate Jobs']
                if job_type == 'Internships':
                    job_type = jobType['Internships']
                job_url = employer_url + '/jobs/' + job_slug + '/'

                with open('hkgc_employers.csv', 'a', newline='') as f:
                    f = csv.writer(f)
                    f.writerow([
                        employer_name,
                        employer_url,
                        job_title,
                        job_description,
                        job_url,
                        job_type
                    ])

        return data


with open('hkgc_employers.csv', 'w', newline='') as file:
    fieldnames = [
        'Employer Name',
        'Employer Profile Link',
        'Job Title',
        'Job Description',
        'Job Link',
        'Job Type'
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
