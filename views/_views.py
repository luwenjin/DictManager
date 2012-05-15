# coding: utf-8
""" Views 中用得到的内容函数 """
import math

from flask import session

from models import tokens, wn_token_coll, dc_token_coll, yd_simple_token_coll, qj_token_coll
from settings import COURSE_LIST, FLAW_LIST, EDITOR_LIST

def make_sidebar_info(request):
    course = request.args.get('course', 'ALL')
    flaw = request.args.get('flaw', 'ALL')
    editor = request.args.get('editor')
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 15))
    search_word = request.args.get('search_word', '')

    query = {}

    if course != 'ALL':
        query['courses'] = course

    if flaw == 'NO_EXPLAIN':
        query['exps_cn'] = []
    elif flaw=='NO_CORE':
        query['exp_core'] = {'$in':[None, u'']}
    elif flaw == 'NOT_PHRASE':
        query['is_phrase'] = False
    elif flaw == 'IS_MARKED':
        query['mark'] = True

    if editor:
        query['last_editor'] = editor

    if search_word:
        query['low'] = unicode(search_word.lower())

    if session['role'] == u'editor':
        query['_id'] = {}
        query['_id']['$gte'], query['_id']['$lte'] = session['token_range']
        query['courses'] = 'IELTS'

    total_count = tokens.Token.find(query).count()
    skip = min(
        max( (page - 1) * count, 0),
        max( total_count - 1, 0)
    )
    token_list = list(tokens.Token.find(query, sort=[('low',1)]).limit(count).skip(skip))

    total_page = int(math.ceil(total_count/ count))

    pager = {
        'current': page,
        'total': total_page
    }

    return {
        'course_list': COURSE_LIST,
        'flaw_list': FLAW_LIST,
        'editor_list': EDITOR_LIST,
        'token_list': token_list,
        'pager': pager,
        'search_word': search_word,
        }


def get_reference_tokens(en):
    results = []
    # wordnet
    wn_token = wn_token_coll.WNToken.find_one({'en': en})
    if wn_token:
        results.append({
            'src': 'wn',
            'exp': u'<br/>'.join([u'[%(count)s:%(synset_token)s] %(POS)s. %(text)s' % x for x in wn_token.exps ])
        })
    # dict.cn
    dc_token = dc_token_coll.DCToken.find_one({'en': en})
    if dc_token:
        results.append({
            'src': 'dc',
            'exp': '<br/>'.join([x.get('exp','') for x in dc_token.exp_sentences])
        })
        #        print results
        print dc_token.exp_sentences
    # youdao
    yd_token = yd_simple_token_coll.YDSimpleToken.find_one({'en': en})
    if yd_token:
        results.append({
            'src': 'yd',
            'exp': '<br/>'.join(yd_token.exps_cn)
        })
    # qiji
    qj_tokens = qj_token_coll.QJToken.find({'en':en})
    exp_map = {}
    for qj_token in qj_tokens:
        exp_map.setdefault(qj_token.exp, [])
        exp_map[qj_token.exp].append('q:'+unicode(qj_token.book()))
    for exp in exp_map:
        src_li = exp_map[exp]
        results.append({
            'src': '<br/>'.join(src_li),
            'exp': exp,
            })
    return results