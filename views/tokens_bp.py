#coding:utf-8
from flask import Blueprint, session, request, render_template, redirect, flash
from mongokit import ObjectId

from models import tokens, Sentence, Token
from _views import query_info, get_reference_tokens, require_login, require_admin

bp = Blueprint('tokens', __name__)

@bp.route('', methods=['GET'])
@require_admin
def view_token():
    page_info = query_info(request)
    print page_info
    search_word = request.args.get('search_word', '').strip()
    token_id = request.args.get('token_id')

    if search_word and page_info['pager']['total'] > 0:
        token = page_info['token_list'][0]
    elif token_id and token_id != 'None':
        token = tokens.Token.find_one(ObjectId(token_id))
        if not token:
            token = page_info['token_list'][0]
    else:
        token = page_info['token_list'][0]

    reference_tokens = get_reference_tokens(token.en)

    return render_template(
        'tokens.html',
        channel = 'token',
        page_info = page_info,
        token = token,
        sentence_list = Sentence.get_token_sentences(token),
        references_tokens = reference_tokens,
    )

@bp.route('', methods=['POST'])
@require_admin
def save_token():
    en = request.form.get('en', '').strip()
    token_id = request.form.get('id')
    exp_core = request.form.get('exp_core')
    courses = [ x.strip() for x in request.form.getlist('course') if x ]
    note = request.form.get('note').strip()
    is_trash = request.form.get('is_trash')

    if token_id:
        token = Token.one(ObjectId(token_id))
        if token:
            if en and token.en != en:
                token.en = en

            token.courses = courses
            token.note = note
            token.exp.core = exp_core
            token.is_trash = True if is_trash else False
            token.save()
            print token
    flash(u'已成功保存', 'alert-success')
    return redirect(request.headers.get('referer'))