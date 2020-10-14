from sshtunnel import SSHTunnelForwarder
import pymongo
from fuzzywuzzy import fuzz, process

MONGO_HOST = "178.128.31.252"
MONGO_DB = "courses_etl"
MONGO_USER = "root"
MONGO_PASS = "oEiw$t^Zx&3w"


def get_terms():
    '''
    :return: all of the terms or program_name in mongodb under collection studyfield_mapping
    '''
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
    '''
    :param course_item: list of study fields to check, use course_item for course_item['rawStudyfield']
    :param list_to_match: all of the terms from mongodb
    :return: None
    '''
    acceptable_ratio = 85
    for item in course_item['rawStudyfield']:
        matched_term = process.extract(item, list_to_match, limit=1, scorer=fuzz.token_sort_ratio)
        term, ratio = matched_term[0]
        matched_term2 = process.extract(item, list_to_match, limit=1, scorer=fuzz.token_set_ratio)
        term2, ratio2 = matched_term2[0]
        matched_term3 = process.extract(item, list_to_match, limit=1, scorer=fuzz.ratio)
        term3, ratio3 = matched_term3[0]
        matched_term4 = process.extract(item, list_to_match, limit=1, scorer=fuzz.UWRatio)
        term4, ratio4 = matched_term4[0]
        if ratio >= acceptable_ratio and item != term:
            course_item['rawStudyfield'].remove(item)
            course_item['rawStudyfield'].append(term)
            course_item.add_flag('rawStudyfield', 'Token Sort, Match Ratio: ' + str(ratio))
            course_item.add_flag('rawStudyfield', 'Token Set, Match Ratio: ' + str(ratio2))
            course_item.add_flag('rawStudyfield', 'Normal Ratio, Match Ratio: ' + str(ratio3))
            course_item.add_flag('rawStudyfield', 'UW Ratio, Match Ratio: ' + str(ratio4))
