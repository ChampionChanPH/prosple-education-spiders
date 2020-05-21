# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re
from .misc_functions import *

class Scholarship(scrapy.Item):
    source_url = scrapy.Field()
    uid = scrapy.Field()
    name = scrapy.Field()
    code = scrapy.Field()
    canonical_group = scrapy.Field()
    time_zone = scrapy.Field()
    provider_name = scrapy.Field()
    eligible = scrapy.Field()
    degree_types = scrapy.Field()
    campus_names = scrapy.Field()
    study_mode = scrapy.Field()
    length_support = scrapy.Field()
    total_value = scrapy.Field()
    expired = scrapy.Field()
    study_field = scrapy.Field()
    overview = scrapy.Field()
    summary = scrapy.Field()
    eligibility = scrapy.Field()
    criteria = scrapy.Field()
    app_process = scrapy.Field()
    retention = scrapy.Field()
    gender = scrapy.Field()
    prior_qualification = scrapy.Field()
    international_apps = scrapy.Field()
    opens = scrapy.Field()
    closes = scrapy.Field()
    starts = scrapy.Field()
    count = scrapy.Field()
    count_description = scrapy.Field()
    frequency = scrapy.Field()
    apply_url = scrapy.Field()
    apply_email = scrapy.Field()
    published = scrapy.Field()


class Rating(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    institution = scrapy.Field()
    url = scrapy.Field()
    level = scrapy.Field()
    studyField = scrapy.Field()
    overallQuality = scrapy.Field()
    teachingQuality = scrapy.Field()
    learnerEngagement = scrapy.Field()
    learningResources = scrapy.Field()
    studentSupport = scrapy.Field()
    skillsDevelopment = scrapy.Field()
    overallSatisfaction = scrapy.Field()
    teachingScale = scrapy.Field()
    skillsScale = scrapy.Field()
    fullTimeEmployment = scrapy.Field()
    overallEmployment = scrapy.Field()
    fullTimeStudy = scrapy.Field()
    medianSalary = scrapy.Field()


class Course(scrapy.Item):

    flag = scrapy.Field()  # Non cms field. contains list of potential errors during scrape.
    # {"field name" : "short description"} eg. {"courseName": "full course name too long. could be a double degree"}

    # Set by function
    rawStudyfield = scrapy.Field()  # non cms field to store program name : List of raw study field, all lowercase
    courseLevel = scrapy.Field()  # Course level : Postgraduate or Undergraduate
    degreeType = scrapy.Field()  # Degree type : Bachelor or Certificate etc
    specificStudyField = scrapy.Field()  # Specific study field. Websites own classifications
    group = scrapy.Field()  # group : Integer corresponding to group
    canonicalGroup = scrapy.Field()  # Canonical Group : String. Name of canonical group.
    uid = scrapy.Field()  # UID

    # Priority Fields (Required) #
    published = scrapy.Field()  # Published : 1 or 0
    institution = scrapy.Field()  # Institution name
    courseName = scrapy.Field()  # Full course name
    lastUpdate = scrapy.Field()  # Data last updated : mm/dd/yy
    sourceURL = scrapy.Field()  # Record Source URL
    campusNID = scrapy.Field()  # Campus NID : Pipe separated string of ids of campuses e.g. "154|345|454"

    # Important Fields (Fill as much as you can. Can be blank if info is not availablem#
    courseCode = scrapy.Field()  # Course code
    cricosCode = scrapy.Field()  # CRICOS code
    internationalApps = scrapy.Field()  # Accept International Applications : 1 or 0
    modeOfStudy = scrapy.Field()  # Mode of study : In person or Online
    startMonths = scrapy.Field()  # Starting months : Pipe separated string of start months. e.g. 01|05|10
    durationRaw = scrapy.Field()  # Non cms field. Content for further parsing
    teachingPeriod = scrapy.Field()  # Teaching period : Number corresponding to teaching period. e.g. 1 for year, 2 for semester
    durationMinFull = scrapy.Field()  # Duration min full-time : Decimal value of duration
    durationMinPart = scrapy.Field()  # Duration min part-time : Decimal value of duration
    durationMaxFull = scrapy.Field()  # Duration max full-time : Decimal value of duration
    durationMaxPart = scrapy.Field()  # Duration max part-time : Decimal value of duration
    feesRaw = scrapy.Field()  # Non cms field. Content for further parsing
    domesticFeeAnnual = scrapy.Field()  # Domestic full fees - annual : Decimal value of fee
    domesticFeeTotal = scrapy.Field()  # Domestic full fees - total : Decimal value of fee
    domesticSubFeeAnnual = scrapy.Field()  # Domestic subsidised fees - annual : Decimal value of fee
    domesticSubFeeTotal = scrapy.Field()  # Domestic subsidised fees - total : Decimal value of fee
    internationalFeeAnnual = scrapy.Field()  # International full fees - annual : Decimal value of fee
    internationalFeeTotal = scrapy.Field()  # International full fees - total : Decimal value of fee
    expired = scrapy.Field()  # Expired
    overviewSummary = scrapy.Field()  # Overview (summary)
    overview = scrapy.Field()  # Overview
    domesticApplyURL = scrapy.Field()  # Domestic apply by URL : course page url.
    domesticApplyEmail = scrapy.Field()  # Domestic apply by form email
    internationalApplyURL = scrapy.Field()  # International apply by URL : course page url.
    internationalApplyEmail = scrapy.Field()  # International apply by form email
    studyField = scrapy.Field()  # Study Field : leave blank. Will be filled by flow

    # Lower priority fields #
    faculty = scrapy.Field()  # Faculty name
    creditTransfer = scrapy.Field()  # Credit for prior study or work
    careerPathways = scrapy.Field()  # Career pathways
    entryRequirements = scrapy.Field()  # Entry requirements
    howToApply = scrapy.Field()  # How to apply
    courseStructure = scrapy.Field()  # Course Structure
    whatLearn = scrapy.Field()  # What you will learn
    finSupportSchemes = scrapy.Field()  # Financial support schemes

    qilt = scrapy.Field()  # QILT Study Field
    postNumerals = scrapy.Field()  # Post numerals
    researchTrainingScheme = scrapy.Field()  # Research training scheme
    doubleDegree = scrapy.Field()  # Double degree : 1 or 0
    guaranteedEntryScore = scrapy.Field()  # Guaranteed entry score
    minPriorQualification = scrapy.Field()  # Minimum prior qualification
    loanSchemes = scrapy.Field()  # Loan schemes
    basicDetails = scrapy.Field()  # BASIC DETAILS
    sectionOverview = scrapy.Field()  # OVERVIEW SECTION
    sectionEntryRequirements = scrapy.Field()  # ENTRY REQUIREMENTS SECTION
    sectionApplicationDetails = scrapy.Field()  # APPLICATION DETAILS SECTION
    sectionFinSupport = scrapy.Field()  # FINANCIAL SUPPORT SECTION
    helperFields = scrapy.Field()  # HELPER FIELDS
    overviewRaw = scrapy.Field()  # Overview Raw
    manualBody = scrapy.Field()  # Manual Body
    seo = scrapy.Field()  # SEO
    lowestScore = scrapy.Field()  # Lowest score to receive an offer
    medianScore = scrapy.Field()  # Median score to receive an offer
    highestScore = scrapy.Field()  # Highest score to receive an offer
    minScoreNextIntake = scrapy.Field()  # Minimum score required for consideration for next intake

    raw_degrees_map = {
        "associate degree": "1",
        "bachelor": "2",
        "bachelor (honours)": "3",
        "certificate": "4",
        "diploma": "5",
        "doctor": "6",
        "graduate certificate": "7",
        "graduate diploma": "8",
        "high school certificate": "9",
        "juris doctor": "10",
        "masters (coursework)": "11",
        "masters (research)": "12",
        "non-award": "13",
        "professional certificate": "14",
        "no match": "15"
    }

    # level is for course level. rank is for double degree selection logic
    degrees = {
        "1": {"level": "1", "rank": 1},
        "2": {"level": "1", "rank": 1},
        "3": {"level": "2", "rank": 2},
        "4": {"level": "1", "rank": 1},
        "5": {"level": "1", "rank": 1},
        "6": {"level": "2", "rank": 2},
        "7": {"level": "2", "rank": 2},
        "8": {"level": "2", "rank": 2},
        "9": {"level": "1", "rank": 1},
        "10": {"level": "2", "rank": 2},
        "11": {"level": "2", "rank": 2},
        "12": {"level": "2", "rank": 2},
        "13": {"level": "1", "rank": 1},
        "14": {"level": "1", "rank": 1},
        "15": {"level": "1", "rank": 99}
    }

    groups = {
        "1": {"num": 3, "name": "The Uni Guide"},
        "2": {"num": 4, "name": "PostgradAustralia"}
    }

    def set_sf_dt(self, new_degrees_map=raw_degrees_map, degree_delims=["/"], type_delims=["of", "in"]):
        '''
        Sets raw study field, specific study field, degree type, course level, group, and canonical group
        :param degrees_map: dictionary; degree mapping
        :param type_delims: Optional; Default = ["of", "in"]; list of possible delimiters between degree type and study field. e.g. ["of","in","-"]
        :param degree_delims: Optional; Default = ["/"]; list of possible double degree delimiters. e.g. ["/",",","-"]
        :return:
        '''

        degrees_map = self.raw_degrees_map
        degrees_map.update(new_degrees_map)
        type_delims = [" " + x + " " for x in type_delims]
        study_fields = []
        # raw_degree_types = []
        rank = 999
        ranges = []
        final_ranges = []

        degree_matches = [re.finditer(x + " ", self["courseName"].lower()) for x in list(degrees_map.keys()) if re.search(x + " ", self["courseName"].lower())]
        if degree_matches:
            for match in degree_matches:
                for r in match:
                    ranges += list(range(r.start(), r.end()))
            ranges = sorted(list(set(ranges)))

            # print(ranges)
            for i in ranges:
                if ranges.index(i) == 0:
                    lower = i
                    upper = i
                elif ranges[-1] == i:
                    final_ranges.append([lower, i])
                else:
                    if i == upper + 1:
                        upper = i
                    else:
                        final_ranges.append([lower, upper])
                        lower = i
                        upper = i
            # print(final_ranges)
            degree_matches = [self["courseName"].lower()[x[0]:x[1]] for x in final_ranges]

        else:
            degree_matches = ["non-award"]
            self.add_flag("degreeType", "There was no degree type match found for: " + self["courseName"])

        # print(degree_matches)
        names = []
        if len(degree_matches) > 2:
            print(str(len(degree_matches)) + " degrees were found.")
            self.add_flag("degreeType", str(len(degree_matches)) + " degree types were found for: " + self["courseName"])
            degree_matches = degree_matches[:2]

        if len(degree_matches) == 2:
            self["doubleDegree"] = 1
            for delim in degree_delims:
                pattern = "\s?"+delim+"\s?(?="+degree_matches[1]+")"
                holder = re.split(pattern, self["courseName"], flags=re.IGNORECASE)
                if len(holder) == 2:
                    names = holder[:]
                    break
        elif len(degree_matches) == 1:
            names = [self["courseName"]]

        # print(names)
        # print(names)

        # delim =
        # single_chars = [x for x in degree_delims if len(x) == 1 or (len(x) == 2 and "\\" in x)]  # Isolate single character delimiter like "/", "-"
        # words = [x for x in degree_delims if len(x) != 1 and "\\" not in x]  # Isolate word delimiters like "and"
        # words = [x for x in words if re.search(x + "\s(?=" + "|".join(list(degrees_map.keys()))+")", self["courseName"].lower(), flags=re.IGNORECASE)]  #get word followed by degree that has a match in the course name
        #
        # if len(words) == 1:
        #     pattern = "\s"+words[0]+"\s(?="+"|".join(list(degrees_map.keys()))+")"  # set pattern for word case
        #
        # elif len(words) > 1:
        #     self.add_flag("doubleDegree", "Matched multiple degree delims "+", ".join(words))  # matching on two delimiters is odd. need to flag
        #
        # elif len(single_chars) > 0:
        #     pattern = "(?<!graduate)\s?["+"".join(single_chars)+"]\s?(?="+"|".join(list(degrees_map.keys()))+")"  # if no match on the word delims and single char delims not empty
        #
        # else:
        #     pattern = None  # if no word delim or single character delim match
        #
        # if pattern:
        #     names = re.split(pattern, self["courseName"], flags=re.IGNORECASE)
        #     names = [x for x in names if x]  # Remove None values when using space as delimiter
        # else:
        #     names = [self["courseName"]]

        # if len(names) == 2:
        #     self["doubleDegree"] = 1
        #
        # elif len(names) > 2:
        #     self.add_flag("doubleDegree", "Course name was split into 3 or more degrees: "+self["courseName"])
        #
        # # Master of Engineering in Biotech
        # delims = [x for x in type_delims if re.search("^(?=" + "|".join(list(degrees_map.keys())) + ")\s" + x + "\s", self["courseName"].lower(), flags=re.IGNORECASE)]  # get word followed by degree that has a match in the course name
        #
        for i in range(len(names)):
            if degree_matches[i] == "non-award":
                study_field = names[i]
            else:
                name = names[i][len(degree_matches[i]):]
                delims = [x for x in type_delims if re.search("^" + x, name.lower())]
                if len(delims) == 1:
                    study_field = name[len(delims[0]):]

                else:
                    self.add_flag("studyField", "No type delimiter match: " + self["courseName"])
                    study_field = cleanspace(name)

            study_fields.append(study_field)

        if len(study_fields) > 0:
            self["rawStudyfield"] = [x.lower() for x in study_fields]
            self["specificStudyField"] = "/".join(study_fields)

        for index in range(len(degree_matches)):
        # for index in range(len(raw_degree_types)):
            # try:
            #     degree_match = max([x for x in list(dict.fromkeys(degrees_map)) if x in raw_degree_types[index]], key=len)  # match degree type and get longest match
            # except ValueError:
            #     if raw_degree_types[index] == "non-award":
            #         degree_match = "non-award"
            #
            #     else:
            #         degree_match = "no match"
            #         self.add_flag("degreeType", "no degree type match for "+raw_degree_types[index])

            degree_match = degrees_map[degree_matches[index]]
            if callable(degree_match):
                degree_match = degree_match(self)

            if rank > self.degrees[degree_match]["rank"]:
                self["degreeType"] = degree_match
                rank = self.degrees[degree_match]["rank"]
                if "honour" in names[index].lower() and self["degreeType"] != "3" and "doubleDegree" not in self:
                    self.add_flag("degreeType", "This could be an honours degree: "+self["courseName"])

        self["courseLevel"] = self.degrees[self["degreeType"]]["level"]
        self["group"] = self.groups[self["courseLevel"]]["num"]
        self["canonicalGroup"] = self.groups[self["courseLevel"]]["name"]

    def add_flag(self, field, message):

        if "flag" not in self:
            self["flag"] = {}

        if field in list(dict.fromkeys(self["flag"]).keys()):
            self["flag"][field].append(message)
        else:
            self["flag"][field] = [message]

    def set_course_name(self, name, prefix):
        self["courseName"] = re.sub("\s+", " ", name)
        self["uid"] = prefix + re.sub(" ", "-", self["courseName"])

    def set_summary(self, text):
        text = re.split("(?<=[\.\?])\s", text)
        if len(text) == 1:
            if len(text[0]) < 250:
                self["overviewSummary"] = text[0]
            else:
                self["overviewSummary"] = text[0][:250]
        if len(text) > 1:
            if len(text[0] + " " + text[1]) < 250:
                self["overviewSummary"] = text[0] + " " + text[1]
            elif len(text[0]) < 250:
                self["overviewSummary"] = text[0]
            else:
                cut_summary = text[0][:250]
                last_space = cut_summary.rindex(" ")
                self["overviewSummary"] = cut_summary[:last_space] + "..."


