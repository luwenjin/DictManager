# coding: utf-8
""" Views 中用得到的内容函数 和一些 view decorators """
import math
import time
from pymongo.collection import Collection
from functools import wraps

from flask import session, current_app, request, redirect

from models import db, Token, wn_token_coll, dc_token_coll, yd_simple_token_coll, qj_token_coll, User

from utils import json_encoder


def query_page(coll_or_model, query, sort=None, page=1, count=20):
    total_count = coll_or_model.find(query).count()
    skip = min(
        max((page - 1) * count, 0),
        max(total_count - 1, 0)
    )
    docs = coll_or_model.find(query, sort=sort).limit(count).skip(skip)
    total_page = int(math.floor(total_count / count)) + 1
    pager = {
        'current': min(page, total_page),
        'total': total_page,
    }
    return list(docs), pager


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
    user = db.User.find_one(name=user_name)
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