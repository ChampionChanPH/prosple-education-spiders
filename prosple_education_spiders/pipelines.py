# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
from .taxonomy import *

class CoursesPipeline(object):
    def process_item(self, item, spider):
        # Replace coded values with values from taxonomy
        taxonomy_fields = ["degreeType", "courseLevel"]
        for field in taxonomy_fields:
            if field in item and re.match("\d+", item[field]):
                item[field] = taxonomies[field][item[field]]

        # Clean out special characters
        fields_to_clean = [
            "whatLearn",
            "overview",
            "overviewSummary",
            "careerPathways",
            "entryRequirements",
            "courseStructure",
            "creditTransfer",
            "courseName",
            "uid",
            "specificStudyField",
            "rawStudyfield"
        ]

        for field in [x for x in fields_to_clean if x in item]:
            for char in list(special_chars.keys()):
                item[field] = item[field].replace(char, special_chars[char])

        return item
