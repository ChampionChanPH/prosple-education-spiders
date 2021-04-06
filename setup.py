# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name='project',
    version='1.0',
    packages=find_packages(),
    package_data={
        'prosple_education_spiders': ['resources/*.json']
    },
    entry_points={'scrapy': ['settings = prosple_education_spiders.settings']},
)