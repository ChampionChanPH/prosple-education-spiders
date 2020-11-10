# by Christian Anasco

import re
from lxml.html.clean import clean_html


def strip_tags(phrase, remove_all_tags=True, remove_hyperlinks=False):
    """
    :param phrase: string to clean
    :param remove_all_tags: if True, remove all HTML tags. if False, h1, h2, h3,
    and h4 tags will be converted to strong tag. Other tags will also be cleaned.
    :param remove_hyperlinks: if True, will remove all of the hyperlinks <a> on that field.
    :return: cleaned phrase
    """

    if remove_all_tags:
        phrase = re.sub("(\r\n\t)", "", phrase, re.M | re.DOTALL)
        phrase = re.sub("</?.*?>", "", phrase, re.M | re.DOTALL)
        return phrase.strip()
    else:
        phrase = re.sub("</[h]{1}[1-4]{1}.*?>", "</strong>", phrase, re.M | re.DOTALL)
        phrase = re.sub("<[h]{1}[1-4]{1}.*?>", "<strong>", phrase, re.M | re.DOTALL)
        phrase = re.sub("</[h]{1}[5-6]{1}.*?>", "</p>", phrase, re.M | re.DOTALL)
        phrase = re.sub("<[h]{1}[5-6]{1}.*?>", "<p>", phrase, re.M | re.DOTALL)
        phrase = re.sub("</(span|div).*?>", "</div>", phrase, re.M | re.DOTALL)
        phrase = re.sub("<(span|div).*?>", "<div>", phrase, re.M | re.DOTALL)
        phrase = re.sub("</p.*?>", "</p>", phrase, re.M | re.DOTALL)
        phrase = re.sub("<p.*?>", "<p>", phrase, re.M | re.DOTALL)
        phrase = re.sub("</li.*?>", "</li>", phrase, re.M | re.DOTALL)
        phrase = re.sub("<li.*?>", "<li>", phrase, re.M | re.DOTALL)
        phrase = re.sub("<img.*?>", "", phrase, re.M | re.DOTALL)
        if remove_hyperlinks:
            phrase = re.sub("</?a.*?>", "", phrase, re.M | re.DOTALL)
        if phrase:
            phrase = clean_html(phrase)
        return phrase.strip()


def __check_alpha(word):
    """
    :param word: word to check if first character is a symbol or not
    :return: same word but already in proper case
    """
    if len(word) == 1:
        return word
    elif word[0].isalpha():
        return word[0].upper() + word[1:].lower()
    else:
        return word[0:2].upper() + word[2:].lower()


def make_proper(sentence):
    """
    :param sentence: any sentence you wanted to make a proper case for titles, course names, etc.
    :return: same sentence in proper case
    """
    all_upper = ['I', 'II', 'III', 'IV', 'VCAL']
    all_lower = ['in', 'to', 'and', 'the', 'of', 'by']

    word_split = re.split(' ', sentence)
    word_split = [x for x in word_split if x != '']

    new_word = []
    for index, item in enumerate(word_split):
        if len(item) > 1 and re.search('-', item):
            item_split = re.split('-', item)
            item_split = [__check_alpha(x) for x in item_split]
            new_word.append('-'.join(item_split))
        elif index == 0:
            new_word.append(__check_alpha(item))
        elif item.upper() in all_upper:
            new_word.append(item.upper())
        elif item.lower() in all_lower:
            new_word.append(item.lower())
        else:
            new_word.append(__check_alpha(item))

    return ' '.join(new_word)
