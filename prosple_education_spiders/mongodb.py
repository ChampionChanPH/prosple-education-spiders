from sshtunnel import SSHTunnelForwarder
import pymongo
from fuzzywuzzy import fuzz, process

MONGO_HOST = "178.128.31.252"
MONGO_DB = "courses_etl"
MONGO_USER = "root"
MONGO_PASS = "oEiw$t^Zx&3w"


def get_terms():
    """
    :return: all of the terms or program_name in mongodb under collection studyfield_mapping
    """
    server = SSHTunnelForwarder(
        MONGO_HOST,
        ssh_username=MONGO_USER,
        ssh_password=MONGO_PASS,
        remote_bind_address=('127.0.0.1', 27017)
    )

    server.daemon_forward_servers = True
    server.start()

    client = pymongo.MongoClient('127.0.0.1', server.local_bind_port)  # server.local_bind_port is assigned local port
    db = client[MONGO_DB]
    coll = db['studyfield_mapping']
    term = coll.distinct("program_name")

    server.stop()

    return term


def update_matches(course_item, list_to_match):
    """
    :param course_item: list of study fields to check, use course_item for course_item['rawStudyfield']
    :param list_to_match: all of the terms from mongodb
    :return: None
    """
    acceptable_ratio = 85
    for item in course_item['rawStudyfield']:
        matched_term = process.extract(item, list_to_match, limit=1, scorer=fuzz.token_sort_ratio)
        term, ratio = matched_term[0]
        spaces = item.count(' ')
        if spaces <= 2:
            if ratio >= acceptable_ratio + 6 and item != term:
                course_item['rawStudyfield'].remove(item)
                course_item['rawStudyfield'].append(term)
                course_item.add_flag('rawStudyfield', 'Match Ratio: ' + str(ratio))
        else:
            if ratio >= acceptable_ratio and item != term:
                course_item['rawStudyfield'].remove(item)
                course_item['rawStudyfield'].append(term)
                course_item.add_flag('rawStudyfield', 'Match Ratio: ' + str(ratio))
