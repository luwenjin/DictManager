#coding:utf-8
import time

from flask import Blueprint, session, request, render_template, redirect, flash, url_for
from mongokit import ObjectId

from models import tokens, Sentence, Token, CoreExp
from _views import to_json, get_reference_tokens, require_login, get_current_user, require_admin, query_page

bp = Blueprint('coreexp', __name__)


def suggest_next(user_name):
    ce = CoreExp.one({
        'options.voters': {'$ne': user_name},
        'skippers': {'$ne': user_name},
    })
    return ce


@bp.route('', methods=['GET'])
@require_login
def redirect_next():
    user = get_current_user()
    ce = suggest_next(user.name)
    if ce:
        return redirect(url_for('.show', en=ce.en))
    else:
        return redirect(url_for('.finish'))


@bp.route('/en/<en>', methods=['GET'])
@require_login
def show(en):
    user = get_current_user()
    ce = CoreExp.one(en=en)
    total = CoreExp.query().count()
    edit_count = CoreExp.query({'options.editor': user.name}).count()
    vote_count = CoreExp.query({'options.voters': user.name}).count() - edit_count
    refs = get_reference_tokens(ce.en)
    token = Token.one(en=en)

    return render_template('coreexp.html',
        ce = ce,
        token = token,
        refs = refs,
        edit_count = edit_count,
        vote_count = vote_count,
        total = total
    )


@bp.route('/finish', methods=['GET'])
@require_login
def finish():
    user = get_current_user()
    return u'<h1 style="display:block;text-align:center;font-size:72px; margin: 0px;padding:0px;">' \
           u'搞定</h1><p style="display:block;text-align:center;">Thanks, %s' \
           u'<br/> %s' \
           u'</p>' % (user.name, user._id)


@bp.route('/save', methods=['GET', 'POST'])
@require_login
@to_json
def save_submit():
    _id = request.values.get('_id')
    option = request.values.get('option')
    skip = request.values.get('skip')
    user = get_current_user()

    ce = CoreExp.one(ObjectId(_id))
    if ce:
        if option:
            option = option.strip()
            ce.add_option(option, user.name)
        elif skip:
            ce.add_skip(user.name)
        ce.save()

    next_ce = suggest_next(user.name)
    if next_ce:
        url = url_for('.show', en=next_ce.en)
    else:
        url = url_for('.finish')

    return {'status': 'ok', 'next_url': url}



@bp.route('/list', methods=['GET'])
@require_admin
def list_core_exp():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 20))

    ce_list, pager = query_page(CoreExp, {}, [('_id',1)], page, count)

    return render_template('core_exp_list.html',
        ce_list = ce_list,
        pager = pager
    )


@bp.route('/option/tag', methods=['GET', 'POST'])
@require_admin
@to_json
def tag_option():
    cn = request.values.get('option')
    tag = request.values.get('tag')
    _id = request.values.get('_id')

    ce = CoreExp.one(ObjectId(_id))
    if not ce:
        return {'status': 'error', 'message': 'not found'}

    for option in ce.options:
        if option['cn'] == cn:
            if tag:
                option['tag'] = tag
            else:
                option['tag'] = None
            ce.save()
            return {'status': 'ok'}

    return {'status': 'error', 'message': 'option not found'}
