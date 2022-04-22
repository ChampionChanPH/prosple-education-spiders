# -*- coding: utf-8 -*-
# by Christian Anasco

from ..standard_libs import *
from ..scratch_file import *


class EcuscholarshipSpiderSpider(scrapy.Spider):
    name = 'ecuscholarship_spider'
    start_urls = ['https://www.ecu.edu.au/scholarships/offers']
    institution = "Edith Cowan University (ECU)"

    def parse(self, response):
        pass
