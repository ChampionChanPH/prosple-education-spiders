# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re

class CoursesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class Course(scrapy.Item):

    flag = scrapy.Field()  # Non cms field. contains list of potential errors during scrape.
    # {"field name" : "short description"} eg. {"courseName": "full course name too long. could be a double degree"}

    # Priority Fields (Required) #
    group = scrapy.Field()  # group : Integer corresponding to group
    canonicalGroup = scrapy.Field()  # Canonical Group : String. Name of canonical group.
    published = scrapy.Field()  # Published : 1 or 0
    courseName = scrapy.Field()  # Full course name
    institution = scrapy.Field()  # Institution name
    rawStudyfield = scrapy.Field()  # non cms field to store program name : List of raw study field, all lowercase
    campusNID = scrapy.Field()  # Campus NID : Pipe separated string of ids of campuses e.g. "154|345|454"
    uid = scrapy.Field()  # UID
    courseLevel = scrapy.Field()  # Course level : Postgraduate or Undergraduate
    degreeType = scrapy.Field()  # Degree type : Bachelor or Certificate etc
    lastUpdate = scrapy.Field()  # Data last updated : mm/dd/yy
    sourceURL = scrapy.Field()  # Record Source URL
    courseCode = scrapy.Field()  # Course code

    # Important Fields (Fill as much as you can. Can be blank if info is not availablem#
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

    specificStudyField = scrapy.Field()  # Specific study field. Websites own classifications
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

    def set_sf_dt(self, degrees, type_delims=["of", "in"], degree_delims=["/"]):
        '''
        :param degrees: dictionary; degree mapping
        :param type_delims: Optional; Default = ["of", "in"]; list of possible delimiters between degree type and study field. e.g. ["of","in","-"]
        :param degree_delims: Optional; Default = ["/"]; list of possible double degree delimiters. e.g. ["/",",","-"]
        :return:
        '''

        self["rawStudyfield"] = []
        raw_degree_types = []
        rank = 999

        single_chars = [x for x in degree_delims if len(x) == 1]  # Isolate single character delimiter like "/", "-"
        words = [x for x in degree_delims if len(x) != 1]  # Isolate word delimiters like "and"
        words = [x for x in words if re.match("\s" + x + "\s(?=" + "|".join(list(degrees.keys())))]  #get word followed by degree that has a match in the course name
        if len(words) == 1:
            pattern = "\s"+words[0]+"\s(?="+"|".join(list(degrees.keys()))  # set pattern for word case

        elif len(words) > 1:
            self.add_flag("doubleDegree", "Matched multiple degree delims"+words)  # matching on two delimiters is odd. need to flag

        else:
            pattern = "\s?["+"".join(single_chars)+"]\s?(?="+"|".join(list(degrees.keys()))+")"  # if no match on the word delims, default to single char delims

        names = re.split(pattern, self["courseName"], flags=re.IGNORECASE)
        if len(names) > 1:
            self["doubleDegree"] = 1

        # Master of Engineering in Biotech
        study_field_holder = []
        delims = type_delims[:]
        for name in names:
            degree_types = [name.split(x, 1)[0].strip(" ") for x in delims]  # [Master, Master of Engineering]
            degree_type = min(degree_types, key=len)
            study_fields = [y[-1].strip(" ") for y in [name.split(x, 1) for x in delims] if len(y) == 2]  # try both delimiters but discard if length of split is 1 (i.e. delimiter not present in string)

            try:
                study_field = max(study_fields, key=len)
                study_field_holder.append(study_field)
                self["rawStudyfield"].append(study_field.lower())
                raw_degree_types.append(degree_type.lower())
            except ValueError:
                self["rawStudyfield"].append(name.lower())
                raw_degree_types.append("non-award")
        if len(study_field_holder) > 0:
            self["specificStudyField"] = "/".join(study_field_holder)

        for index in range(len(raw_degree_types)):
            try:
                degree_match = max([x for x in list(dict.fromkeys(degrees)) if x in raw_degree_types[index]], key=len)  # match degree type and get longest match
            except ValueError:
                degree_match = "no match"
                self.add_flag("degreeType", "no degree type match for "+raw_degree_types[index])

            if rank > degrees[degree_match]["rank"]:
                self["degreeType"] = degrees[degree_match]["type"]
                if callable(self["degreeType"]):
                    self["degreeType"] = self["degreeType"](self)
                rank = degrees[degree_match]["rank"]

    def add_flag(self, field, message):

        if "flag" not in self:
            self["flag"] = {}

        if field in list(dict.fromkeys(self["flag"]).keys()):
            self["flag"][field].append(message)
        else:
            self["flag"][field] = [message]

