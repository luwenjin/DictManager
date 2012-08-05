# coding: utf-8
""" Views 中用得到的内容函数 和一些 view decorators """
import math
import time
from pymongo.collection import Collection
from functools import wraps

from flask import session, current_app, request, redirect

from models import Token, wn_token_coll, dc_token_coll, yd_simple_token_coll, qj_token_coll, User
from settings import COURSE_LIST, FLAW_LIST
from utils import json_encoder


def query_page(coll_or_model, query, sort=None, page=1, count=20):
    if type(coll_or_model) == Collection:
        finder = coll_or_model.find
    else:
        finder = coll_or_model.coll_model().find

    total_count = finder(query).count()
    skip = min(
        max((page - 1) * count, 0),
        max(total_count - 1, 0)
    )
    docs = finder(query, sort=sort).limit(count).skip(skip)
    total_page = int(math.floor(total_count / count)) + 1
    pager = {
        'current': min(page, total_page),
        'total': total_page,
    }
    return list(docs), pager


def query_info(request):
    course = request.args.get('course', 'ALL')
    flaw = request.args.get('flaw', 'ALL')
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 15))
    search_word = request.args.get('search_word', '')

    query = {}

    if course != 'ALL':
        query['courses'] = course

    if flaw == 'NO_EXPLAIN':
        query['exp.cn'] = []
    elif flaw == 'NO_CORE':
        query['exp.core'] = {'$in': [None, u'']}
    elif flaw == 'NOT_PHRASE':
        query['type'] = u'phrase'

    if search_word:
        query['hash'] = Token.make_hash(search_word)

    token_list, pager = query_page(Token, query, [('hash', 1)], page, count)

    return {
        'course_list': COURSE_LIST,
        'flaw_list': FLAW_LIST,
        'token_list': token_list,
        'pager': pager,
        'search_word': search_word,
        }


def get_reference_tokens(en):
    results = []
    t = time.time()
    # wordnet
    wn_token_coll.ensure_index('en')
    wn_token = wn_token_coll.find_one({'en': en})
    if wn_token:
        results.append({
            'src': 'wn',
            'exp': u'<br/>'.join(
                [u'[常见度%(count)s: %(synset_token)s] %(POS)s. %(text)s' % x for x in wn_token.get('exps', [])]
            )
        })

    # dict.cn
    dc_token_coll.ensure_index('en')
    dc_token = dc_token_coll.find_one({'en': en})
    if dc_token:
        results.append({
            'src': 'dc',
            'exp': '<br/>'.join(
                [x.get('exp', '') for x in dc_token.get('exp_sentences', [])]
            )
        })

    # youdao
    yd_simple_token_coll.ensure_index('en')
    yd_token = yd_simple_token_coll.find_one({'en': en})
    if yd_token:
        results.append({
            'src': 'yd',
            'exp': '<br/>'.join(yd_token.get('exps_cn', []))
        })

    # qiji
    qj_token_coll.ensure_index('en')
    qj_tokens = qj_token_coll.find({'en': en})
    exp_map = {}
    for qj_token in qj_tokens:
        exp_map.setdefault(qj_token['exp'], [])
        exp_map[qj_token['exp']].append('q: %s' % qj_token.get('course_id'))
    for exp in exp_map:
        src_li = exp_map[exp]
        results.append({
            'src': '<br/>'.join(src_li),
            'exp': exp,
            })
#    print 'get_reference_tokens:', time.time()-t
    return results


def get_current_user():
    user_name = session.get('name')
    user = User.one(name=user_name)
    return user


def to_json(f):
    @wraps(f)
    def decorated_function(*args, **kwds):
        result = f(*args, **kwds)
        return current_app.response_class(
            json_encoder.encode(result, indent=None if request.is_xhr else 2),
            mimetype='application/json'
        )

    return decorated_function


def require_login(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user:
            return fn(*args, **kwargs)
        else:
            return redirect('/login')

    return decorated_function


def require_admin(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user and user.role == u'admin':
            return fn(*args, **kwargs)
        else:
            return redirect('/login')

    return decorated_function