# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
from .taxonomy import *

class CoursesPipeline(object):
    def process_item(self, item, spider):
        if "degreeType" in item and re.match("\d+", item["degreeType"]):
            item["degreeType"] = taxonomy_degree_types[item["degreeType"]]
        return item
