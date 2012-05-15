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

from models import users, tokens, dc_page_coll
from utils import tojson
from views import tokens_blueprints

app = Flask(__name__)
app.config.from_object('settings')
app.register_blueprint( tokens_blueprints, url_prefix='/tokens')

app.jinja_env.filters['max'] = max
app.jinja_env.filters['min'] = min

assets = Environment(app)



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

