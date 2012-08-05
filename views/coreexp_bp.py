#coding:utf-8
import time
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for
from mongokit import ObjectId

from models import Token, CoreExp, Score
from _views import to_json, get_reference_tokens, require_login, get_current_user, require_admin, query_page

bp = Blueprint('coreexp', __name__)

MAX_TASKS = 200
MIN_VOTES = 7
MAX_VOTES = 15


# todo: 导入其他翻译的前3个解释，每个词性取3个（用;,分割）


def user_done_count(user_name):
    count = CoreExp.query({
        'options.voters': user_name,
        'tags': {'$ne': u'hidden'},
        }).count()
    return count


def suggest_next(user_name):
    t = time.time()
    done_count = user_done_count(user_name)
    if done_count >= MAX_TASKS:
        return None
    else:
        print 'suggest_next:', time.time() - t
        query = {
            'options.voters': {'$ne': user_name},
            'tags': {'$nin': [u'hidden', u'full']},
            }
        ce = CoreExp.one(query, sort=[('_id', 1)])
        return ce


@bp.route('', methods=['GET'])
@require_login
def go_next():
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
    total = MAX_TASKS
    vote_count = user_done_count(user.name)
    refs = get_reference_tokens(ce.en)
    token = Token.one(en=en)

    return render_template('coreexp.html',
        ce=ce,
        token=token,
        refs=refs,
        vote_count=vote_count,
        total=total
    )


@bp.route('/save', methods=['GET', 'POST'])
@require_login
@to_json
def add_option():
    t = time.time()
    _id = request.values.get('_id')
    option_cn = request.values.get('option', u'')
    time_cost = int(request.values.get('time', 0))
    user = get_current_user()
    ip = request.remote_addr

    ce = CoreExp.one(ObjectId(_id))
    if ce:
        ce.add_option(option_cn, user.name)
        ce.add_log(
            user = user.name,
            op = 'AddOption',
            option = option_cn,
            time_cost = time_cost,
            ip = ip,
        )
        if ip not in ce.voters_ip:
            ce.voters_ip.append(ip)

        if ce.actions_count >= MAX_VOTES:
            ce.add_tag(u'full')
        elif ce.actions_count >= MIN_VOTES:
            if len(ce.best_option['voters']) >= ce.actions_count * 0.6:
                ce.add_tag(u'full')
        ce.save()
        print ce
    else:
        return {'status': 'error', 'message': '没找到这个单词'}

    next_ce = suggest_next(user.name)
    if next_ce:
        url = url_for('.show', en=next_ce.en)
    else:
        url = url_for('.finish')

    print 'add_option', time.time() - t
    return {'status': 'ok', 'next_url': url}


@bp.route('/finish', methods=['GET'])
@require_login
def finish():
    user = get_current_user()
    count = user_done_count(user.name)
    if count > 3:
        return u'<h1 style="display:block;text-align:center;font-size:72px; margin: 0px;padding:0px;">'\
               u'搞定%s个</h1><p style="display:block;text-align:center;">Thanks, %s'\
               u'<br/> %s'\
               u'<br/> 如果你觉得这个网站比较有意义，想更深入地参与，或者有什么意见和建议'\
               u'<br/> 请加群：253362251，认证信息填写猪八戒上面的ID'\
               u'</p>' % (count, user.name, user._id)
    else:
        return u'<h1 style="display:block;text-align:center;font-size:72px; margin: 0px;padding:0px;">'\
               u'抱歉，已经截稿了</h1><p style="display:block;text-align:center;">Thanks, %s'\
               u'<br/> %s'\
               u'</p>' % (user.name, user._id)


@bp.route('/list', methods=['GET'])
@require_admin
def list_ce():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 20))
    user_name = request.args.get('user')
    tags = request.args.get('tags', 'all').split(',')

    query = {'$and': []}
    for tag in tags:
        if not tag:
            continue
        elif tag == u'all':
            query = {}
            break

        if tag[0] == '-':
            tag = tag[1:]
            query['$and'].append({'tags': {'$ne': tag}})
        else:
            query['$and'].append({'tags': tag})

    if user_name:
        query.setdefault('$and', [])
        query['$and'].append({'options.voters': user_name})

    ce_list, pager = query_page(CoreExp, query, [('_id', 1)], page, count)

    return render_template('core_exp-list.html',
        ce_list=ce_list,
        pager=pager
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


@bp.route('/tag', methods=['GET', 'POST'])
@require_admin
@to_json
def tag_ce():
    _id = request.values.get('_id')
    tag = request.values.get('tag')
    action = request.values.get('action')

    ce = CoreExp.one(ObjectId(_id))
    if not ce:
        return {'status': 'error', 'message': 'not found'}

    if action == 'add':
        if tag not in ce.tags:
            ce.add_tag(tag)
            ce.save()
        return {'status': 'ok'}
    elif action == 'del':
        if tag in ce.tags:
            ce.remove_tag(tag)
            ce.save()
        return {'status': 'ok'}
    else:
        return {'status': 'error', 'message': 'invalid action'}


@bp.route('/scores/refresh')
@require_admin
def refresh_scores():
    # log start from 8.1 14:00
    d = {}
    user_logs = {}

    Score.coll().drop()
    for ce in CoreExp.query({'tags': {'$ne': u'hidden'}, 'actions_count': {'$gt': 0}}):
        if not ce.logs or ce.logs[0]['time'] < datetime(2012, 8, 1, 12):
            continue

        best_option = ce.best_option
        for log in ce.get('logs', []):
            user_name = log['user']
            user_logs.setdefault(user_name, [])
            user_logs[user_name].append(log)

        for option in ce.options:
            voters = option['voters']
            for voter in voters:
                d.setdefault(voter, {'score': 0, 'vote': 0, 'total': 0, 'seconds': 0})
                d[voter]['total'] += 1
                if ce.en == u'drug':
                    print option['voters']
                if voter == u'a_n_89757':
                    print voter

            if best_option and option['cn'] == best_option['cn']:
                for i, voter in enumerate(voters):
                    d[voter]['score'] += 1
                    d[voter]['vote'] += 1

    for user_name in d:
        if user_name == u'SYS':
            continue
        score = Score.one(user=user_name, project=u'coreexp')
        if not score:
            score = Score.new(user=user_name, project=u'coreexp')

        logs = sorted(user_logs[user_name], key=lambda x: x.get('time'))
        for i, log in enumerate(logs):
            if not i:
                continue
            seconds = (log['time'] - logs[i - 1]['time']).seconds
            if seconds <= 240:
                d[user_name]['seconds'] += seconds

        score.score = d[user_name]['score']
        score.details = d[user_name]
        score.save()

    return redirect(url_for('.scores'))


@bp.route('/scores')
@require_admin
def scores():
    scores = Score.all({'user': {'$nin': [u'admin', u'SYS']}}, sort=[('score', -1)])
    return render_template('core_exp-scores.html', scores=scores)


@bp.route('/list/auto_hide')
@require_admin
def auto_hide():
    """hide all full ce"""
    query = {'$and': [
            {'tags': {'$ne': u'hidden'}},
            {'tags': u'full'},
    ]}
    for ce in CoreExp.query(query):
        ce.add_tag(u'hidden')
        ce.save()
    return redirect(request.headers.get('referer'))