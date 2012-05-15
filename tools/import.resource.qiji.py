#coding:utf-8
import sys
import os
from pprint import pprint
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------

import sqlite3

from models import db, Sentence, Token, tokens, \
    qj_course_coll, QJCourse, qj_token_coll, QJToken, qj_sentence_coll, QJSentence
from lang_utils import extract_meaning_objects

sql_conn = sqlite3.connect('../../resources/dicts/words.sqlite')
sql_conn.row_factory = sqlite3.Row


QJ_COURSES = [
    ( 197, 'CET4', '《新大学英语教学大纲》四级' ),
    ( 198, 'CET6', '《新大学英语教学大纲》六级' ),
    ( 203, 'CET4', '《四级考试词汇必备》' ),
    ( 209, 'YJS', '《2006研究生入学考试大纲》' ),
    ( 210, 'GMAT', '《GMAT600分词汇》' ),
    ( 211, 'GMAT', '《GMAT600分词组》' ),
    ( 212, 'GMAT', '《GMAT800分常考词汇》' ),
    ( 213, 'GMAT', '《GMAT800分商业管理词汇》' ),
    ( 214, 'GRE', '《GRE字汇进阶》(上)' ),
    ( 215, 'GRE', '《GRE字汇进阶》(下)' ),
    ( 216, 'GRE', '《太傻单词》' ),
    ( 217, 'GRE', '《最新GRE词汇》' ),
    ( 218, 'TOEFL', '《TOEFL阅读词汇笔记》(一)' ),
    ( 219, 'TOEFL', '《TOEFL阅读词汇笔记》(二)' ),
    ( 220, 'TOEFL', '《TOEFL阅读词汇笔记》(三)' ),
    ( 221, 'TOEFL', '《托福600分单字》(牢记)' ),
    ( 222, 'TOEFL', '《托福600分单字》(其他)' ),
    ( 223, 'TOEFL', '《新版TOEFL词汇精选》' ),
    ( 224, 'TOEFL', '《最新TOEFL词汇》' ),
    ( 225, 'TOEFL', '《最新TOEFL词组》' ),
    ( 233, 'TOEIC', '《TOEIC托业单词》' ),
    ( 313, 'YJS', '《2010年考研英语大纲》' ),
    ( 316, 'IELTS', '《最新雅思考试词汇必备2009年更新》' ),
    ( 317, 'GK', '《高考英语考试大纲词汇表2009》' ),
    ( 319, 'IELTS', '《2009雅思考试核心词汇》' ),
    ( 320, 'IELTS', '《2009雅思考试词汇必备》' ),
    ( 322, 'CET4', '《2009大学英语四级教学大纲》' ),
    ( 323, 'CET6', '《2009大学英语六级教学大纲》' ),
]

course_map = {}
c = sql_conn.cursor()
c.execute("select course_id, category_id, course_name from course")
for i, row in enumerate(c.fetchall()):
    course_id, category_id, book_name = row
    course_map[course_id] = {
        'category_id': category_id,
        'book_name': book_name
    }

def get_course_name(course_id):
    for li in QJ_COURSES:
        if li[0] == course_id:
            return unicode(li[1])
    return None

def get_category(category_id):
    cur = sql_conn.cursor()
    cur.execute("select name from categoryinfo where id=?", (category_id,))
    row = cur.fetchone()
    category = row[0]
    return category


def import_courses():
    qj_course_coll.drop()

    cur = sql_conn.cursor()
    cur.execute("select course_id, category_id, course_name as book from course")

    for i, row in enumerate(cur.fetchall()):
        course_id, category_id, book = row
        category = get_category(category_id)
        course_name = get_course_name(course_id)

        doc = qj_course_coll.QJCourse()
        doc.id = course_id
        doc.name = course_name
        doc.category = category
        doc.book = book
        doc.save()
        print i, doc


def import_tokens():
    qj_token_coll.drop()

    cur = sql_conn.cursor()
    cur.execute('''select
    english as en,
    chinese as exp,
    phonetic as ph_en,
    phonetic_us as ph_us,
    dict_word_id,
    word_id,
    course_id
    from wordinfo
    ''')
    for i, row in enumerate(cur.fetchall()):
        doc = qj_token_coll.QJToken()
        doc.en, \
        doc.exp, \
        doc.ph_en, \
        doc.ph_us,\
        doc.dict_word_id, \
        doc.word_id, \
        doc.course_id = row
        doc.save()
        print i, doc.en

def load_tokens(course_name=None):
    '''全部导入正式库， 本库同一个dict_word_id不会对应2个拼写不同的单词，本函数目前只能用作初次导入'''
    qj_course_coll.ensure_index('id')
    if course_name:
        course_ids = [x.get('id') for x in qj_course_coll.QJCourse.find({'name': course_name})]
    else:
        course_ids = qj_course_coll.distinct('id')

    qj_token_coll.ensure_index('course_id')
    qj_token_coll.ensure_index('en')

#    print list(qj_course_coll.find())
#    print course_ids
    en_list = qj_token_coll.find({'course_id': {'$in': course_ids}}).distinct('en')
    for i, en in enumerate(en_list):
        qj_token_list = list(qj_token_coll.QJToken.find({'en': en}))
        token = Token.get_token(en)
#        print token
        if not token:
            token = db.tokens.Token()
            token.en = en
            token.ph_us = max([x.get('ph_us') for x in qj_token_list])
            token.ph_en = max([x.get('ph_en') for x in qj_token_list])

            course_ids = [x.get('course_id') for x in qj_token_list]
            course_names = set([get_course_name(x) for x in course_ids])
            token.courses = [x for x in  course_names if x]
            token.src = u'qiji'

            token.save()
            print i, en


def import_sentences():
    qj_sentence_coll.drop()

    print 'Preparing word_map...'
    word_map = {}
    word_cursor = sql_conn.cursor()
    word_cursor.execute('select english, dict_word_id from wordinfo')
    for row in word_cursor.fetchall():
        en, id = row
        word_map[id] = en

    cur = sql_conn.cursor()
    cur.execute("select "
                "sentence_id as id, "
                "english as en, "
                "chinese as cn "
                "from sentence")
    for i, row in enumerate(cur.fetchall()):
        doc = qj_sentence_coll.QJSentence()
        doc.id, \
        doc.en, \
        doc.cn = row

        cur2 = sql_conn.cursor()
        cur2.execute("select dict_word_id from word_sentence where sentence_id=?", (doc.id,))
        dict_word_ids = [ x[0] for x in cur2.fetchall()]
        en_list= [ word_map[x] for x in dict_word_ids ]

        doc.include = list(set(en_list))
        doc.save()

        print doc.include
        print i, doc.en


def load_sentences():
    qj_sentence_list = list(qj_sentence_coll.QJSentence.find())
    qj_token_coll.ensure_index('dict_word_id')
    for i, qj_sentence in enumerate(qj_sentence_list):
        # 对比正式库，是否有同样的句子
        hash = Sentence.get_hash(qj_sentence.en)
        sentence = db.sentences.Sentence.find_one({'hash': hash})
        if not sentence:
            # 无同样句子则新增
            sentence = db.sentences.Sentence()
            sentence.en, sentence.cn = qj_sentence.en, qj_sentence.cn
        #更新正式库中句子的对应单词列表
        en_set = set(qj_sentence.include)
        en_set.update(sentence.include)
        sentence.include = list(en_set)
        sentence.save()

        print i, sentence.en


def import_differences():
    # todo: not ready
#    sample = {
#        'mutual': unicode,
#        'dict_word_ids': [int],
#        'differences': [{'word': unicode, 'meaning': unicode}]
#    }
    coll = db['resource.qiji.differences']
    coll.drop()

    c = sql_conn.cursor()
    c.execute("select id, dict_word_id, content from discriminate")
    group_map = {}
    for i, row in enumerate(c.fetchall()):
        id, dict_word_id, mutual = row
        group_map.setdefault(mutual, [])
        group_map[mutual].append({
            'discriminate_id': id,
            'dict_word_id': dict_word_id,
        })

    c = sql_conn.cursor()
    c.execute("select discriminate_id, Discriminate_details_id from discriminate_relation")
    dr_map = {}
    for i, row in enumerate(c.fetchall()):
        discriminate_id, detail_id = row
        dr_map.setdefault(discriminate_id, [])
        dr_map[discriminate_id].append(detail_id)

    c = sql_conn.cursor()
    c.execute("select id, word, discriminate from discriminate_details")
    dd_map = {}
    for i, row in enumerate(c.fetchall()):
        detail_id, word, meaning = row
        dd_map[detail_id] = (word, meaning)

    for mutual in group_map:
        mutual = unicode(mutual.strip())
        dict_word_ids = [item.get('dict_word_id') for item in group_map[mutual]]

        discriminate_ids = [item.get('discriminate_id') for item in group_map[mutual]]
        detail_ids_groups = [dr_map[discriminate_id] for discriminate_id in discriminate_ids]
#        for detail_ids in detail_ids_groups:
#            if detail_ids != detail_ids_groups[0]:
#                print detail_ids_groups
        differences = []
        for detail_id in detail_ids_groups[0]:
            print detail_id
            differences.append({
                'word': unicode(dd_map[detail_id][0].strip()),
                'meaning': unicode(dd_map[detail_id][1].strip())
            })

        doc = {
            'mutual': mutual,
            'dict_word_ids': dict_word_ids,
            'differences': differences
        }

        coll.save(doc)
        print doc

def match_differences_dict_word_id():
    # todo: not ready
    '''
    测试differences中的word和dict_word_id取到的单词能否对应起来
    '''
    differences = db['resource.qiji.differences']
    tokens = db['resource.qiji.tokens']
    tokens.ensure_index('dict_word_id')
    tokens.ensure_index('foreign')
    for doc in differences.find():
        ids = doc.get('dict_word_ids')
        words = [x.get('word') for x in doc.get('differences')]
        meanings = [x.get('meaning') for x in doc.get('differences')]

        for word in words:
            token = tokens.find_one({'foreign': word})
            if not token:
                print '-----------------------', doc.get("_id")
                for item in doc.get('differences'):
                    if item.get('word') == word:
                        print '!!!',
                    print item.get('word'), item.get('meaning')
                print ids

def repair_differences_word_error():
    # todo: not ready
    ''' data from match_differences_dict_word_id(), some data has typos'''
    data = {
        'dlight': 'delight',
        'farwell': 'farewell',
        'frfuse': 'refuse',
        'flaour': 'flavour',
        'pefection': 'perfection',
        'devor': 'devour',
        'radom': "random",
        'econmic': 'economic',
        'districk': 'district',
        'ridiclous': 'ridiculous',
        'supicion': 'suspicion',
        'fifle': 'rifle',
        'disordr': 'disorder',
        'laguage': 'language',
        'stum': 'stun',
        'neighbourbood': 'neighbourhood',
        'tolerantj': 'tolerant',
        'burricane': 'hurricane',
        'wepon': 'weapon',
        'frightem': 'frighten',
        'rgeister': 'register',
        'siggle': 'giggle',
        'programe': 'programme',
        'recolect': 'recollect',
        'hoblly': 'hobby',
        'ambigous': 'ambiguous',
        'Father': "father",
        'offent': 'offend',
        'transfrom': 'transform',
        'throug': 'throng',
    }
    differences = db['resource.qiji.differences']
    differences.ensure_index('differences.word')
    for typo in data:
        word = data[typo]
        doc = differences.find_one({'differences.word': typo})
        for item in doc['differences']:
            if item['word'] == typo:
                item['word'] = word
        differences.save(doc)

def clear_duplicate_differences():
    # todo: not ready
    differences = db['resource.qiji.differences']
    words = differences.distinct("differences.word")
    dup_docs = {}
    for word in words:
        doc_list = list(differences.find({'differences.word': word}))
        if len(doc_list) > 1:

            for doc in doc_list:
                for doc2 in doc_list:
                    if doc.get('_id') >= doc2.get('_id'):
                        continue
                    set1 = set([x.get('word') for x in doc.get("differences")])
                    set2 = set([x.get('word') for x in doc2.get("differences")])
                    if set1.issubset(set2):
                        print '=================='
                        pprint(doc2)
                        print '--'
                        pprint(doc)
                        dup_docs[doc.get("_id")] = doc
    for doc in dup_docs:
        differences.remove(doc)


if __name__ == '__main__':
#    import_courses()
#    import_tokens()
#    import_sentences()
#
#    import_differences()
#    repair_differences_word_error()
#    clear_duplicate_differences()
#
#    db.tokens.drop()
#    load_tokens()
#
#    db.sentences.drop()
#    load_sentences()