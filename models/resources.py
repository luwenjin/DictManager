#coding:utf-8
'''导入资源的 Documents'''
from datetime import datetime

from mongokit import Document

from ._base import DB_NAME, db, \
    qj_course_coll, qj_sentence_coll, qj_token_coll, \
    dc_page_coll, dc_token_coll, \
    yd_detail_page_coll, yd_simple_token_coll, \
    cl_page_coll, cl_token_coll,\
    wn_token_coll


class QJToken(Document):
    __database__ = DB_NAME
    __collection__ = qj_token_coll.name
    structure = {
        'en': unicode,
        'exp': unicode,
        'ph_en': unicode,
        'ph_us': unicode,
        'dict_word_id': int,
        'word_id': int,
        'course_id': int,
    }
    indexes = [
        {'fields': ['en']},
        {'fields': ['course_id']},
        {'fields': ['dict_word_id']}
    ]
    use_dot_notation = True

    def book(self):
        course = qj_course_coll.QJCourse.find_one({'id': self.course_id})
        if course:
            return course.get('book', None)


class QJCourse(Document):
    __database__ = DB_NAME
    __collection__ = qj_course_coll.name
    structure = {
        'id': int,
        'name': unicode,
        'book': unicode,
        'category': unicode,
    }
    indexes = [
            {'fields': ['id']},
            {'fields': ['name']}
    ]
    use_dot_notation = True


class QJSentence(Document):
    __database__ = DB_NAME
    __collection__ = qj_sentence_coll.name
    structure = {
        'id': int,
        'en': unicode,
        'cn': unicode,
        'include': [unicode],
        }
    indexes = [
            {'fields': ['id']},
            {'fields': ['include']}
    ]
    use_dot_notation = True

class DCPage(Document):
    __database__ = DB_NAME
    __collection__ = dc_page_coll.name
    structure = {
        'en': unicode,
        'content': unicode,
        'saved': bool
    }
    default_values = {
        'saved': False,
        'content': None,
        }
    indexes = [
            {'fields': ['en']},
    ]
    use_dot_notation = True

class DCToken(Document):
    __database__ = DB_NAME
    __collection__ = dc_token_coll.name
    structure = {
        'en': unicode,
        'seg': unicode, #en的分段情况
        'level': int, #常见程度，5最高，1最低
        'phs': [unicode], #音标列表

        'forms': {unicode: unicode},  # 词性：拼写
        'exp_sentences':[{
            'exp': unicode,
            'sentences': [{'en': unicode, 'cn':unicode}],
        }],
    }
    default_values = {
        'seg': None,
        'level': None,
        'phs': [],
        'forms': None,
        'exp_sentences': [],
#        'exp_sentences.sentences': []
        }
    indexes = [
            {'fields': ['en']},
    ]
    use_dot_notation = True

class WNToken(Document):
    __database__ = DB_NAME
    __collection__ = wn_token_coll.name
    structure = {
        'en': unicode,
        'exps': [{
            'POS': unicode,
            'text': unicode,
            'synset_token': unicode,  #Synset('leaf.v.03') => leaf
            'count': int
        }]
        }
    default_values = {
        'exps': []
    }
    indexes = [
            {'fields': ['en']},
    ]
    use_dot_notation = True

class Page(Document):
    __database__ = DB_NAME
    structure = {
        'en': unicode,
        'content': unicode,
        }
    default_values = {
        'content': None,
        }
    indexes = [
            {'fields': ['en']},
    ]
    use_dot_notation = True

class YDSimpleToken(Document):
    __database__ = DB_NAME
    __collection__ = yd_simple_token_coll.name
    structure = {
        'en': unicode,
        'return_en': unicode,
        'phs': [unicode],
        'speech': unicode,
        'exps_cn': [unicode],
        'forms': [{'type': unicode, 'text': unicode}],
        'stem': unicode,
        'rels': [{
            'POS': unicode,
            'words': [{
                'en': unicode, 'cn': unicode}]
            }]
        }
    default_values = {
        'forms': [],
        'rels': [],
        }
    indexes = [
            {'fields': ['en']},
    ]
    use_dot_notation = True

class YDRelWords(Document):
    pass


class CLToken(Document):
    __database__ = DB_NAME
    __collection__ = cl_token_coll.name
    structure = {
        'en': unicode,
        'current': float,
        'band': int,
        }
    indexes = [
            {'fields': ['en']},
    ]
    use_dot_notation = True
