import re
from time import strptime


def get_period(str_in):
    '''
    :param str_in: period string. eg. months, weeks
    :return: period code
    '''

    periods = {"year": 1, "semester": 2, "trimester": 3, "quarter": 4, "month": 12, "week": 52, "day": 365}
    str_in = str_in.lower()
    if str_in[-1] == "s":
        str_in = str_in[:-1]

    return periods[str_in]


def convert_months(months):
    """
    :param months: list of potential month strings. eg. ["June", "and", "October", "intakes"]
    :return: list of all valid month strings converted to code. eg. ["06", "10"]
    """
    converted = []
    for month in months:
        month = get_month(month)
        if month != "" and str(month).zfill(2) not in converted:
            converted.append(str(month).zfill(2))
    return converted


def filter_html(html_string):
    allowed_tags = [
        "ul",
        "ol",
        "li",
        "p",
        "i",
        "a",
        "h1",
        "h2",
        "h3",
        "h4",
        "strong"
    ]

    re.sub("<.*?>",)
    all_tags = re.finditer("<.*?>",html_string)
    for i in all_tags:
        print(i)


def cleanspace(str_in):
    return re.sub(r'\s+', ' ', str_in).strip(' ')


def get_month(str_in):
    try:
        return strptime(cleanspace(str_in.strip(" ")), '%b').tm_mon

    except ValueError:
        try:
            return strptime(cleanspace(str_in.strip(" ")), '%B').tm_mon

        except ValueError:
            return ""


def unique_list(list_in):
    """
    :param list_in: list with duplicate values
    :return: list with no more duplicates
    """
    return list(dict.fromkeys(list_in))


def campus_NID(campus_map, list_in):
    """
    :param campus_map: dictionary of campus names mapped to node id in cms
    :param list_in: list of campus names
    "return: list of node ids for each campus.
    """
    for i in range(len(list_in)):
        try:
            list_in[i] = campus_map[list_in[i]]

        except KeyError:
            print("Campus name not in Campus Map")

    return list_in
