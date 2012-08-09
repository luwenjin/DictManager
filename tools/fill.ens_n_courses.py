# coding: utf-8
""" import ens and courses"""
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
from models import qj_course_coll, qj_token_coll, Token


def _qj_course_ids(course_name=None):
    qj_course_coll.ensure_index('id')
    qj_token_coll.ensure_index('course_id')
    qj_token_coll.ensure_index('en')
    if course_name:
        course_ids = [x.get('id') for x in qj_course_coll.find({'name': course_name})]
    else:
        course_ids = qj_course_coll.distinct('id')
    return course_ids


def _qj_tokens(course_name):
    course_ids = _qj_course_ids(course_name)
    tokens = qj_token_coll.find({'course_id': {'$in': course_ids}})
    return list(tokens)


def _qj_token_en_list(course_name=None):
    course_ids = _qj_course_ids(course_name)
    token_en_list = qj_token_coll.find({'course_id': {'$in': course_ids}}).distinct('en')
    return token_en_list


def fill_qj_token_en(course_name=None):
    token_en_list = _qj_token_en_list(course_name)
    for i, en in enumerate(token_en_list):
        token = Token.one(en=en)
        if not token:
            Token.insert(en=en)
            print i, 'new:', en
        else:
            print i, 'old', en
            pass


def fill_qj_token_courses():
    for i, token in enumerate(Token.query()):
        qj_tokens = qj_token_coll.find({'en': token.en})
        course_ids = list(set([t.get('course_id') for t in qj_tokens]))
        courses = qj_course_coll.find({'id': {'$in':course_ids}})
        course_names = list(set([c.get('name') for c in courses if c.get('name')]))
        if 1:#course_names and not token.courses:
            token.courses = course_names
            token.save()
            print i, token.en, token.courses


if __name__ == '__main__':
    fill_qj_token_en()
    fill_qj_token_courses()