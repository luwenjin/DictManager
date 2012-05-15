#coding:utf-8
import os
from pprint import pprint
from datetime import datetime
import math
import urllib
import random

from furl import furl
from mongokit import ObjectId
from flask import Flask, request, redirect, render_template, session, flash
from flaskext.assets import Environment

from models import db, users, tokens, sentences, Sentence, \
    dc_page_coll, dc_token_coll, qj_token_coll, yd_simple_token_coll, wn_token_coll

from utils import tojson

app = Flask(__name__)
app.debug = True
app.secret_key = 'DictManager'


app.jinja_env.filters['max'] = max
app.jinja_env.filters['min'] = min

assets = Environment(app)

course_list = [
    'CET4',
    'CET6',
    'YJS',
    'GMAT',
    "GRE",
    "TOEFL",
    "TOEIC",
    "IELTS",
    "GK"
]
flaw_list = [
    'NO_EXPLAIN',
    'NO_CORE',
    'NOT_PHRASE',
    'IS_MARKED',
    ]
editor_list = [
    u'Addie2012',
    u'KeyT',
    u'Sara',
    u'ahdou222',
    u'autumn140',
    u'challenge',
    u'character',
    u'cloud0717',
    u'conan0407',
    u'daisy1201',
    u'dfzhanglimin',
    u'doubleyong37',
    u'editor',
    u'fly明月',
    u'gongyiqin',
    u'huazheng1985',
    u'huyuyi2008',
    u'leileinn2010',
    u'lqcx8888',
    u'lwjhere',
    u'mavis81',
    u'morningcloud17',
    u'nihewo',
    u'penny110716',
    u'pokerpokerpoker',
    u'rualprincess',
    u'sq5156',
    u'try',
    u'vapsy11',
    u'wangmin3598',
    u'whxm4',
    u'winterlovely',
    u'xiaocaoamy',
    u'xuxuenan0306',
    u'yoohi',
    u'刘小畅2012',
    u'向日葵盛开的夏天m',
    u'好晴朗',
    u'如风走过',
    u'学生勤工俭学',
    u'橄榄树',
    u'爱尚体育',
    u'素女女',
    u'调皮的妖妖',
]

@app.route('/r/<path>')
def test(path):
    print path
    return 'ok'

@app.route('/', methods=['GET'])
def index():
    if session.get('name'):
        return redirect('/tokens')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login_or_reg():
    tokens_per_editor = 100
    name = request.form.get('name')
    password = request.form.get('password')
    user = users.User.find_one({"name": name})
    if user:
        print user.password, password
        if user.password != password:
            return redirect('/login?error=%s'%urllib.quote('密码不正确'))
        if user.ban:
            return redirect('/login?error=%s'%urllib.quote('您已经被禁止登录'))
    else:
        user = users.User()
        user.name = name
        user.password = password
        user.role = u'editor'
        max_token_oid = None
        for old_user in users.User.find():
            if old_user.token_range and old_user.token_range[1] > max_token_oid:
                max_token_oid = old_user.token_range[1]
        default_query = {'courses': 'IELTS'}
        if max_token_oid:
            default_query['_id'] = {'$gt': max_token_oid}
        cur = tokens.Token.find(default_query, sort=[('_id', 1)])

        if cur.count <= tokens_per_editor:
            return redirect('/login?error=%s'%urllib.quote('已超过最大用户数'))
        user.token_range = [cur[0].get('_id'), cur[tokens_per_editor].get('_id')]
        print user.token_range
    session['name'] = user.name
    session['role'] = user.role
    session['token_range'] = user.token_range
    user.last_login = datetime.now()
    user.save()
    return redirect('/tokens')

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
        'course_list': course_list,
        'flaw_list': flaw_list,
        'editor_list': editor_list,
        'token_list': token_list,
        'pager': pager,
        'search_word': search_word,
        }

@app.route('/tokens', methods=['GET'])
def view_token():
    if not session.get('name'):
        return redirect('/login')
    sidebar_info = make_sidebar_info(request)
    search_word = request.args.get('search_word', '').strip()
    token_id = request.args.get('token_id')

    if search_word and sidebar_info['pager']['total'] > 0:
        token = sidebar_info['token_list'][0]
    elif token_id and token_id != 'None':
        token = tokens.Token.find_one(ObjectId(token_id))
        if not token:
            token = sidebar_info['token_list'][0]
    else:
        token = sidebar_info['token_list'][0]

    reference_tokens = get_reference_tokens(token.en)

    return render_template(
        '/tokens.html',
        channel = 'token',
        sidebar = sidebar_info,
        token = token,
        sentence_list = Sentence.get_token_sentences(token),
        references_tokens = reference_tokens,
    )

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
#        print qj_token.book()
        exp_map.setdefault(qj_token.exp, [])
        exp_map[qj_token.exp].append('q:'+unicode(qj_token.book()))
    for exp in exp_map:
        src_li = exp_map[exp]
        results.append({
            'src': '<br/>'.join(src_li),
            'exp': exp,
        })
    return results



@app.route('/tokens', methods=['POST'])
def save_token():
    en = request.form.get('en', '').strip()
    token_id = request.form.get('id')
    exp_core = request.form.get('exp_core')
    courses = [ x.strip() for x in request.form.getlist('course') if x ]
    note = request.form.get('note').strip()
    is_trash = request.form.get('is_trash')

    if token_id:
        token = tokens.Token.find_one(ObjectId(token_id))
        if token:
            if en and token.en != en:
                result = token.rename(en)
                if not result:
                    flash(u'重名：'+en, 'alert-error')
                    return redirect(request.headers.get('referer'))
            if courses:
                token.courses = courses
            token.note = note
            token.exp_core = exp_core
            token.is_trash = True if is_trash else False
            token.last_editor= unicode(session.get('name'))
            token.save()
            print token
    flash(u'已成功保存', 'alert-success')
    return redirect(request.headers.get('referer'))


@app.route('/dictcn/save_and_get', methods=['POST', 'GET'])
@tojson
def save_dict_cn_page_and_get_next():
    en = request.form.get("en")
    content = request.form.get('content')

    dc_page_coll.ensure_index('saved')
    dc_page_coll.ensure_index('en')

    page = dc_page_coll.DCPage.find_one({'en': en})
#    print en, page
    if page:
        page.content = content
        page.saved = True
        page.save()

    unsaved_pages = dc_page_coll.DCPage.find({'saved':False})
    pages_count = unsaved_pages.count()
    print 'unsaved:', pages_count
    page_index = random.randint(0, pages_count-1)
    unsaved_page = unsaved_pages[page_index]
#    print unsaved_page
    if unsaved_page:
        return {
            'status': 'ok',
            'en': unsaved_page['en']
        }
    else:
        return {
            'status': 'end'
        }

