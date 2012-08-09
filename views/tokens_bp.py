#coding:utf-8
from flask import Blueprint, request, render_template, redirect, flash
from mongokit import ObjectId

from models import db, Sentence, Token
from _views import get_reference_tokens, require_admin, query_page
from settings import COURSE_LIST, FLAW_LIST

bp = Blueprint('tokens', __name__)


def query_sidebar_info(request):
    course = request.args.get('course', 'ALL')
    flaw = request.args.get('flaw', 'ALL')
    no_trash = request.args.get('no_trash', '1')
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 15))
    search_word = request.args.get('search_word', '')

    print flaw

    query = []

    if course != 'ALL':
        query.append({'courses': course})

    if flaw == 'NO_EXPLAIN':
        query.append({'exp.cn': []})
    elif flaw == 'NO_CORE':
        query.append({'exp.core': {'$in': [None, u'']}})
    elif flaw == 'WORD':
        query.append({'tags': u'word'})
    elif flaw == 'PHRASE':
        query.append({'tags': u'phrase'})

    if no_trash != '0':
        query.append({'tags': {'$ne': u'trash'}})

    if search_word:
        query.append({'hash': Token.make_hash(search_word)})


    if query:
        full_query = {'$and': query}
    else:
        full_query = {}

    print 'query', query
    print 'full_query', full_query
    token_list, pager = query_page(db.Token, full_query, [('hash', 1)], page, count)

    return {
        'course_list': COURSE_LIST,
        'flaw_list': FLAW_LIST,
        'token_list': token_list,
        'pager': pager,
        'search_word': search_word,
        }



@bp.route('', methods=['GET'])
@require_admin
def view_token():
    page_info = query_sidebar_info(request)
    search_word = request.args.get('search_word', '').strip()
    token_id = request.args.get('token_id')

    if search_word and page_info['pager']['total'] > 0 and page_info['token_list']:
        token = page_info['token_list'][0]
    elif token_id and token_id != 'None':
        token = db.Token.find_one(ObjectId(token_id))
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
        token = db.Token.find_one(ObjectId(token_id))
        if token:
            if en and token.en != en:
                token.en = en

            token.courses = set(courses)
            token.note = note
            token.exp.core = exp_core
            if is_trash:
                token.trash(True)
            else:
                token.trash(False)
            token.save()
    flash(u'已成功保存', 'alert-success')
    return redirect(request.headers.get('referer'))