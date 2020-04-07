# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


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
    courseLevel = scrapy.Field()  # Course level : Graduate or Undergraduate
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

    def set_raw_sf(self):
        self["rawStudyfield"] = []
        self["degreeType"] = []
        if "doubleDegree" in self and self["doubleDegree"] == 1:
            names = self["courseName"].split(" / ")
        else:
            names = [self["courseName"]]

        delims = [" of ", " in "]
        for name in names:
            degree_types = [name.split(x, 1)[0] for x in delims]
            degree_type = min(degree_types, key=len)
            study_fields = [y[-1] for y in [self["courseName"].split(x, 1) for x in delims] if len(y) == 2] #try both delimiters but discard if length of split is 1 (i.e. delimiter not present in string)
            try:
                study_field = max(study_fields, key=len)
                self["rawStudyfield"].append(study_field.lower())
                self["degreeType"].append(degree_type.lower())

            except ValueError:
                self["rawStudyfield"].append(self["courseName"].lower())
                self["degreeType"].append("non-award")

    def add_flag(self, field, message):

        if "flag" not in self:
            self["flag"] = {}

        if field in list(dict.fromkeys(self["flag"])):
            self["flag"][field].append(message)
        else:
            self["flag"][field] = [message]

