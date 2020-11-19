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

    tag_conversion = {
        'h1': 'strong',
        'h2': 'strong',
        'h3': 'strong',
        'h4': 'strong',
        'h5': 'p',
        'h6': 'p',
        'span': 'div',
        'div': 'div',
        'p': 'p',
        'li': 'li',
    }

    if remove_all_tags:
        phrase = re.sub("[\r\n\t]", " ", phrase, re.M | re.DOTALL)
        phrase = re.sub("</?.*?>", "", phrase, re.M | re.DOTALL)
        phrase = re.sub("<.*?>", "", phrase, re.M | re.DOTALL)
        phrase = re.sub("\s+", " ", phrase, re.M | re.DOTALL)
        return phrase.strip()
    else:
        for key, value in tag_conversion.items():
            phrase = re.sub('</' + key + '.*?>', '</' + value + '>', phrase, re.M | re.DOTALL)
            phrase = re.sub('<' + key + '.*?>', '<' + value + '>', phrase, re.M | re.DOTALL)
        phrase = re.sub("<img.*?>", "", phrase, re.M | re.DOTALL)
        if remove_hyperlinks:
            phrase = re.sub("</?a.*?>", "", phrase, re.M | re.DOTALL)
        if phrase:
            phrase = clean_html(phrase)
        return phrase.strip()


def __check_alpha(word, exclude=False, upper_extend=[], lower_extend=[]):
    """
    :param word: word to check if first character is a symbol or not
    :param lower_extend: list of words that you want to include on the all_lower list
    :param upper_extend: list of words that you want to include on the all_upper list
    :return: same word but already in proper case
    """
    all_upper = ['I', 'II', 'III', 'IV', 'VCAL', 'VCE', 'TAFE', 'TESOL', 'ELICOS']
    all_lower = ['in', 'to', 'and', 'the', 'of', 'by']

    if upper_extend:
        all_upper.extend(upper_extend)
    if lower_extend:
        all_lower.extend(lower_extend)

    if len(word) == 1:
        return word
    elif word.upper() in all_upper:
        return word.upper()
    elif word.lower() in all_lower and not exclude:
        return word.lower()
    elif word[0].isalpha():
        return word[0].upper() + word[1:].lower()
    else:
        return word[0:2].upper() + word[2:].lower()


def __word_symbols(word, symbol, upper_extend=[], lower_extend=[]):
    word_split = re.split(symbol, word)
    word_split = [__check_alpha(x, False, upper_extend, lower_extend) for x in word_split if x != '']
    word_split = '-'.join(word_split)
    if re.search('-$', word):
        word_split += '-'
    if re.search('^-', word):
        word_split = '-' + word_split

    return word_split


def make_proper(sentence, upper_extend=[], lower_extend=[]):
    """
    :param sentence: any sentence you wanted to make a proper case for titles, course names, etc.
    :param lower_extend: list of words that you want to include on the all_lower list in __check_alpha function
    :param upper_extend: list of words that you want to include on the all_upper list in __check_alpha function
    :return: same sentence in proper case
    """
    word_split = re.split(' ', sentence)
    word_split = [x for x in word_split if x != '']

    new_word = []
    for index, item in enumerate(word_split):
        if len(item) > 1 and re.search('-', item):
            new_word.append(__word_symbols(item, '-', upper_extend, lower_extend))
        elif len(item) > 1 and re.search('/', item):
            new_word.append(__word_symbols(item, '/', upper_extend, lower_extend))
        elif index == 0:
            new_word.append(__check_alpha(item, True, upper_extend, lower_extend))
        else:
            new_word.append(__check_alpha(item, False, upper_extend, lower_extend))

    return ' '.join(new_word)
