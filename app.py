#coding:utf-8
from datetime import datetime
import urllib

from flask import Flask, request, redirect, render_template, session, url_for
from flask.ext.assets import Environment

from models import User
from views import require_login, tokens_blueprints, coreexp_blueprints

app = Flask(__name__)
app.config.from_object('settings')

app.register_blueprint(tokens_blueprints, url_prefix='/tokens')
app.register_blueprint(coreexp_blueprints, url_prefix='/votes/ce')

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
    return redirect(url_for('coreexp.go_next'))

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_or_register():
    name = request.form.get('name', '').strip()
    password = request.form.get('password', '').strip()

    if not name or not password:
        return redirect('/login?error=%s' % urllib.quote('请输入账号密码'))

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