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
from flask.ext.assets import Environment

from models import User
from views import require_login, tokens_blueprints, coreexp_blueprints

app = Flask(__name__)
app.config.from_object('settings')

app.register_blueprint(tokens_blueprints, url_prefix='/tokens')
app.register_blueprint(coreexp_blueprints, url_prefix='/coreexp')

app.jinja_env.filters['max'] = max
app.jinja_env.filters['min'] = min

assets = Environment(app)


@app.route('/r/<path>')
def test(path):
    print path
    return 'ok'


@app.route('/', methods=['GET'])
@require_login
def index():
    return redirect('/coreexp')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_or_register():
    name = request.form.get('name', '').strip()
    password = request.form.get('password', '').strip()
    user = User.one(name=name)
    if user:
        if user.password != password:
            return redirect('/login?error=%s' % urllib.quote('密码不正确'))
        if user.ban:
            return redirect('/login?error=%s' % urllib.quote('您已经被禁止登录'))
    else:
        user = User.new(
            name = name,
            password = password,
            role = u'editor',
        )
    session['name'] = user.name
    session['role'] = user.role
    user.last_login = datetime.now()
    user.save()
    return redirect('/')