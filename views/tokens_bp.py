#coding:utf-8
from flask import Blueprint, session, request, render_template, redirect, flash
from mongokit import ObjectId

from models import tokens, Sentence
from _views import make_sidebar_info, get_reference_tokens

bp = Blueprint('tokens', __name__)

@bp.route('/', methods=['GET'])
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

@bp.route('/', methods=['POST'])
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