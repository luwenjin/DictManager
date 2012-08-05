# coding: utf-8
""" import all kinds of resources into main db """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
import math
from collections import Counter


from models import db, qj_course_coll, qj_token_coll, qj_sentence_coll, \
    dc_token_coll, yd_simple_token_coll, freq_coll
from models import Token, tokens, Sentence
from views._views import get_reference_tokens
from lang import parse_exp, split_cn



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
            token = Token.insert(en=en)

#            if en != token.en:
#                print i, 'norm:', en, '->', token.en
            print i, 'new:', en
        else:
            print i, 'old', en
            pass


def fill_yd_ph():
    query = { 'phs': [] }
    for i, token in enumerate(Token.query(query)):
        en = token.en

        yd_token = yd_simple_token_coll.find_one({'en': en})
        if yd_token and yd_token['phs']:
            token.phs = yd_token['phs']
            token.save()
            print token.en, token.phs
        else:
            print '.....skip', token.en, token.phs


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


def fill_auto_coreexp():
    for i, token in enumerate(Token.query()):
        if token.core.exp:
            continue

        en = token.en

        counter = Counter()
        refs = get_reference_tokens(token.en)
        for ref in refs:
            if ref['src'] in ['wn']:
                continue

            lines = ref['exp'].split('<br/>')
            items = parse_exp(lines)

            for item in items:
                cn_li = split_cn(item[1])
                for cn in cn_li:
                    if cn:
                        counter[cn] += 1

        for cn, count in counter.most_common(1):
            tpl = (
                '%(total)s\n'
                '%(others)s'
                )

            total = sum(counter.values())
            score = 1.0 * count / total
            others = []
            for j, (s, n) in enumerate(counter.most_common()):
                others.append((s,n))
            others = ','.join([ '%s[%s]' % x for x in others ])
            d = {
                'en': en,
                'cn': cn,
                'count': count,
                'total': total,
                'score': score,
                'others': others
            }
            note = tpl % d

            token.exp.core = cn
            token.note = note
            token.save()
            print i, en, cn



def export_freq_data():
    """填充常见程度，来源主要有2个，google ngram / colins"""
    query = {'type': u'word'}

    ng_coll = db['resource.ngram.1']
    ng_coll.ensure_index('lemmas')
    cl_coll = db['resource.collins.tokens']
    cl_coll.ensure_index('en')

    f = open('data/commonness.txt', 'w+')

    for token in Token.query():
        en = token.en
        ng = ng_coll.find_one({'lemmas':en})
        if not ng:
            ng = {}
        cl = cl_coll.find_one({'en': en})
        if not cl:
            cl = {}
        line = '%s\t%s\t%s\n'%(en, ng.get('count'), cl.get('current'))
        f.write(line.encode('utf-8'))
        try:
            print line,
        except:
            pass
    f.close()


def calc_freq(freq_doc):
    min_max_logs = {
        'cl_hits': [0, 7.431485639],
        'cl_current': [-6.211478113 , 0.748852145],
        'gn_count': [1.806179974, 9.456220367],
    }
    for key in ['cl_hits', 'cl_current', 'gn_count']:
        if freq_doc.has_key(key) and freq_doc[key] > 0:
            val = freq_doc.get(key)
            min_val, max_val = min_max_logs[key]
            log_val = math.log10(val)
            norm_val = (log_val-min_val)/(max_val-min_val)

            if key == 'cl_hits':
                return norm_val
            elif key == 'gn_count':
                return 0.006 + 0.972 * norm_val
            elif key == 'cl_current':
                return 0.011 + 0.969 * (0.006 + 0.972 * norm_val)
            else:
                raise Exception('invalid_key')

    return -1



def fill_all_ranks():
    query = {'freq':-1}
    for i, token in enumerate(tokens.find(query)):
        en = token['en']
        freq_doc = freq_coll.find_one({'en': en})

        freq = calc_freq(freq_doc)
        print en, freq, token['courses']
        if freq > 0:
            token['freq'] = freq
            tokens.save(token)

    print 'left:', tokens.find({'freq': -1}).count()



def update_qj_sentences():
    # todo
    pass




if __name__ == '__main__':

    print tokens.count()



