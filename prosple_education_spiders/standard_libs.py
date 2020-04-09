import scrapy
import re
from .items import Course
from .misc_functions import *
from datetime import date
from time import strptime
from scrapy_splash import SplashRequest