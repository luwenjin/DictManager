# coding: utf-8
""" import all kinds of resources into main db """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
from models import qj_course_coll, qj_token_coll, qj_sentence_coll, dc_token_coll
from models import Token, tokens, Sentence


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


def update_qj_token_en(course_name=None):
    token_en_list = _qj_token_en_list(course_name)
    for i, en in enumerate(token_en_list):
        token = Token.one(en=en)
        if not token:
            Token.insert(en=en)
            print i, 'new:', en
        else:
            print i, 'old', en

def update_qj_token_ph(course_name=None):
    qj_token_coll.ensure_index('en')

    qj_token_en_list = _qj_token_en_list(course_name)
    for i, en in enumerate(qj_token_en_list):
        token = Token.one(en=en)
        if not token:
            raise Exception('token not found: %s' % token.en)


        flag = False
        if not token.ph.en:
            flag = True
            en_token = qj_token_coll.find_one({'en': en, 'ph_en':{'$ne':u''}})
            if en_token:
                token.ph.en = en_token['ph_en']
                token.save()

        if not token.ph.us:
            flag = True
            us_token = qj_token_coll.find_one({'en': en, 'ph_us':{'$ne':u''}})
            if us_token:
                token.ph.us = us_token['ph_us']
                token.save()

        if flag and token.type == 'word':
            print i, token.en, token.ph.en, token.ph.us

def update_qj_token_courses():
    for i, token in enumerate(Token.query()):
        qj_tokens = qj_token_coll.find({'en': token.en})
        course_ids = list(set([t.get('course_id') for t in qj_tokens]))
        courses = qj_course_coll.find({'id': {'$in':course_ids}})
        course_names = list(set([c.get('name') for c in courses if c.get('name')]))
        if 1:#course_names and not token.courses:
            token.courses = course_names
            token.save()
            print i, token.en, token.courses


def update_qj_sentences():
    qj_token_coll.ensure_index('dict_word_id')
    Sentence.coll().ensure_index('hash')

    qj_sentence_list = list(qj_sentence_coll.find())
    for i, qj_sentence in enumerate(qj_sentence_list):
        # 对比正式库，是否有同样的句子
        hash = Sentence.make_hash(qj_sentence['en'])
        sentence = Sentence.one(hash=hash)
        if not sentence:
            # 无同样句子则新增
            sentence = Sentence.insert(
                en = qj_sentence['en'],
                cn = qj_sentence['cn']
            )
            #更新正式库中句子的对应单词列表
        sentence.update_include(qj_sentence['include'])
        sentence.save()
        print i, sentence.include, sentence.en
    print Sentence.coll().count()



if __name__ == '__main__':
#    Sentence.coll().drop()
    update_qj_token_ph()
