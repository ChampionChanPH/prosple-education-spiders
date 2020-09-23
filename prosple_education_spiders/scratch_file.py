import re
from lxml.html.clean import clean_html


def strip_tags(phrase, remove_all_tags=True):
    """
    :param phrase: string to clean
    :param remove_all_tags: if True, remove all HTML tags. if False, h1, h2, h3,
    and h4 tags will be converted to strong tag. Other tags will also be cleaned.
    :return: cleaned phrase
    """

    if remove_all_tags:
        phrase = re.sub("(\r\n\t)", "", phrase, re.M)
        phrase = re.sub("</?.*?>", "", phrase, re.M)
        return phrase.strip()
    else:
        phrase = re.sub("</[h]{1}[1-4]{1}.*?>", "</strong>", phrase, re.DOTALL)
        phrase = re.sub("<[h]{1}[1-4]{1}.*?>", "<strong>", phrase, re.DOTALL)
        phrase = re.sub("</[h]{1}[5-6]{1}.*?>", "</p>", phrase, re.DOTALL)
        phrase = re.sub("<[h]{1}[5-6]{1}.*?>", "<p>", phrase, re.DOTALL)
        phrase = re.sub("<img.*?>", "<p>", phrase, re.DOTALL)
        if phrase:
            phrase = clean_html(phrase)
        return phrase.strip()
