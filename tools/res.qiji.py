#coding:utf-8
import sys
import os
from pprint import pprint

parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#------------------------------------------------------

import sqlite3

from models import db, qj_course_coll, qj_token_coll, qj_sentence_coll


sql_conn = sqlite3.connect('data/words.sqlite')
sql_conn.row_factory = sqlite3.Row

COURSES = [
    ( 197, u'CET4', u'《新大学英语教学大纲》四级' ),
    ( 198, u'CET6', u'《新大学英语教学大纲》六级' ),
    ( 203, u'CET4', u'《四级考试词汇必备》' ),
    ( 209, u'YJS', u'《2006研究生入学考试大纲》' ),
    ( 210, u'GMAT', u'《GMAT600分词汇》' ),
    ( 211, u'GMAT', u'《GMAT600分词组》' ),
    ( 212, u'GMAT', u'《GMAT800分常考词汇》' ),
    ( 213, u'GMAT', u'《GMAT800分商业管理词汇》' ),
    ( 214, u'GRE', u'《GRE字汇进阶》(上)' ),
    ( 215, u'GRE', u'《GRE字汇进阶》(下)' ),
    ( 216, u'GRE', u'《太傻单词》' ),
    ( 217, u'GRE', u'《最新GRE词汇》' ),
    ( 218, u'TOEFL', u'《TOEFL阅读词汇笔记》(一)' ),
    ( 219, u'TOEFL', u'《TOEFL阅读词汇笔记》(二)' ),
    ( 220, u'TOEFL', u'《TOEFL阅读词汇笔记》(三)' ),
    ( 221, u'TOEFL', u'《托福600分单字》(牢记)' ),
    ( 222, u'TOEFL', u'《托福600分单字》(其他)' ),
    ( 223, u'TOEFL', u'《新版TOEFL词汇精选》' ),
    ( 224, u'TOEFL', u'《最新TOEFL词汇》' ),
    ( 225, u'TOEFL', u'《最新TOEFL词组》' ),
    ( 233, u'TOEIC', u'《TOEIC托业单词》' ),
    ( 313, u'YJS', u'《2010年考研英语大纲》' ),
    ( 316, u'IELTS', u'《最新雅思考试词汇必备2009年更新》' ),
    ( 317, u'GK', u'《高考英语考试大纲词汇表2009》' ),
    ( 319, u'IELTS', u'《2009雅思考试核心词汇》' ),
    ( 320, u'IELTS', u'《2009雅思考试词汇必备》' ),
    ( 322, u'CET4', u'《2009大学英语四级教学大纲》' ),
    ( 323, u'CET6', u'《2009大学英语六级教学大纲》' ),
]

#def make_COURSE_MAP():
#    c = sql_conn.cursor()
#    c.execute("select course_id, category_id, course_name from course")
#    # course_id: 课程id, category_id：分类id, course_name: 课程名（中文）
#    for i, row in enumerate(c.fetchall()):
#        course_id, category_id, book_name = row
#        COURSE_MAP[course_id] = {
#            'category_id': category_id,
#            'book_name': book_name
#        }
#COURSE_MAP = make_COURSE_MAP()

# category(小学/初中/高中） is useless here
#def get_category(category_id):
#    cur = sql_conn.cursor()
#    cur.execute("select name from categoryinfo where id=?", (category_id,))
#    row = cur.fetchone()
#    category = row[0]
#    return category


def make_COURSE_MAP():
    doc = {}
    for id, name, label in COURSES:
        doc[id] = {
            'name': name,
            'label': label
        }
    return doc
COURSE_MAP = make_COURSE_MAP()


def get_ssb_course_name(course_id):
    doc = COURSE_MAP.get(course_id)
    if doc:
        return doc['name']
    else:
        return None


def save_courses():
    qj_course_coll.drop()

    cur = sql_conn.cursor()
    cur.execute("select course_id, course_name as label from course")

    for i, row in enumerate(cur.fetchall()):
        course_id, label = row

        doc = {
            'id': course_id,
            'name': get_ssb_course_name(course_id),
            'label': label
        }
        qj_course_coll.save(doc)

def save_tokens():
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
        d = dict()
        d['en'], d['exp'], d['ph_en'], d['ph_us'], d['dict_word_id'], d['word_id'], d['course_id'] = row
        qj_token_coll.save(d)
        print i, d['en']


def save_sentences():
    qj_sentence_coll.drop()

    print 'Preparing dict_word_id->en map...',
    id_en_map = {}
    cur = sql_conn.cursor()
    cur.execute('select english, dict_word_id from wordinfo')
    for row in cur.fetchall():
        en, id = row
        id_en_map[id] = en
    print 'done'

    cur = sql_conn.cursor()
    cur.execute("select "
                "sentence_id as id, "
                "english as en, "
                "chinese as cn "
                "from sentence")
    for i, row in enumerate(cur.fetchall()):
        doc = dict()
        doc['id'], doc['en'], doc['cn'] = row

        cur2 = sql_conn.cursor()
        cur2.execute("select dict_word_id from word_sentence where sentence_id=?", (doc['id'],))
        dict_word_ids = [x[0] for x in cur2.fetchall()]
        en_list = [id_en_map[x] for x in dict_word_ids]
        doc['include'] = list(set(en_list))

        qj_sentence_coll.save(doc)

        print i, doc['en']
        print doc['include']
        print



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
    """
    测试differences中的word和dict_word_id取到的单词能否对应起来
    """
    differences = db['resource.qiji.differences']
    tokens = db['resource.qiji.tokens']
    tokens.ensure_index('dict_word_id')
    tokens.ensure_index('foreign')
    for doc in differences.find():
        ids = doc.get('dict_word_ids')
        words = [x.get('word') for x in doc.get('differences')]
        meanings = [x.get('meaning') for x in doc.get('differences')]

        for word in words:
            token = db.Token.find_one({'foreign': word})
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


#    save_courses()
#    save_tokens()
    save_sentences()
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