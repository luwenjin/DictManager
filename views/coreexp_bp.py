#coding:utf-8
import time
import re
from pprint import pprint

from flask import Blueprint, request, render_template, redirect, url_for
from mongokit import ObjectId

from models import Token, CoreExp, Score
from _views import to_json, get_reference_tokens, require_login, get_current_user, require_admin, query_page

bp = Blueprint('coreexp', __name__)

MAX_TASKS = 200
MAX_VOTES = 10


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
        ce = CoreExp.one({
            'options.voters': {'$ne': user_name},
            'tags': {'$nin': [u'closed', u'hidden', u'full']},
            }, sort=[('_id', 1)])
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


@bp.route('/finish', methods=['GET'])
@require_login
def finish():
    user = get_current_user()
    count = user_done_count(user.name)
    if count > 3:
        return u'<h1 style="display:block;text-align:center;font-size:72px; margin: 0px;padding:0px;">'\
               u'搞定%s个</h1><p style="display:block;text-align:center;">Thanks, %s'\
               u'<br/> %s'\
               u'</p>' % (count, user.name, user._id)
    else:
        return u'<h1 style="display:block;text-align:center;font-size:72px; margin: 0px;padding:0px;">'\
               u'抱歉，已经截稿了</h1><p style="display:block;text-align:center;">Thanks, %s'\
               u'<br/> %s'\
               u'</p>' % (user.name, user._id)


@bp.route('/save', methods=['GET', 'POST'])
@require_login
@to_json
def add_option():
    t = time.time()
    _id = request.values.get('_id')
    option_cn = request.values.get('option', u'')
    user = get_current_user()

    ce = CoreExp.one(ObjectId(_id))
    if ce:
        option_cn = re.sub(u'\s+', u'', option_cn)
        option_cn = re.sub(u'…+', u'…', option_cn)

        seps = [u',', u'，', u'.', u';', u'；', u'、']
        if any([c in option_cn for c in seps]):
            return {'status': 'error', 'message': '仅限提交1个最核心的解释（注意是1个）'}

#        if not option_cn:
#            return {'status': 'error', 'message': '请输入答案'}

        ce.add_option(option_cn, user.name)

        if ce.actions_count > MAX_VOTES:
            ce.add_tag(u'full')
        ce.save()
    else:
        return {'status': 'error', 'message': '没找到这个单词'}

    next_ce = suggest_next(user.name)
    if next_ce:
        url = url_for('.show', en=next_ce.en)
    else:
        url = url_for('.finish')

    print 'add_option', time.time()-t
    return {'status': 'ok', 'next_url': url}


@bp.route('/list', methods=['GET'])
@require_admin
def ce_list():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 20))
    channels = request.args.get('channels', '-closed,-hidden').split(',')
    user_name = request.args.get('user')

    query = {'$and': []}
    for channel in channels:
        if channel == 'all':
            query = {}
            break
        elif channel[0] == '-':
            channel = channel[1:]
            query['$and'].append({'tags': {'$ne': channel}})
        else:
            query['$and'].append({'tags': channel})

    if user_name:
        query.setdefault('$and', [])
        query['$and'].append({'options.voters': user_name})

    print query

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


@bp.route('/list/auto_close')
@require_admin
def auto_close():
    # 只有1个答案的
    query = {
        'tags': {'$ne': u'closed'},
        'options': {'$size': 1},
        'actions_count': {'$gte': MAX_VOTES}
    }
    for ce in CoreExp.query(query):
        ce.tags.append(u'closed')
        ce.save()

#    # 最佳答案占了70%以上的
#    query = {
#        'tags': {'$ne': u'closed'},
#        'actions_count': {'$gt': MAX_ACTIONS_MULTIPLE}
#    }
#    for ce in CoreExp.query(query):
#        if len(ce.best_option['voters']) > ce.actions_count * 0.7:
#            ce.tags.append(u'closed')
#            ce.save()

    # 已经选出最佳答案的
    query = {
        'tags': {'$ne': u'closed'},
        'options.tag': u'best',
        }
    for ce in CoreExp.query(query):
        ce.tags.append(u'closed')
        ce.save()

    return redirect(url_for('.ce_list'))


@bp.route('/list/auto_hide')
@require_admin
def auto_hide():
    # 隐藏所有 closed 的 ce
    auto_close()
    query = {
        '$and': [
                {'tags': u'closed'},
                {'tags': {'$ne': u'hidden'}},
        ]
    }
    for ce in CoreExp.query(query):
        ce.tags.append(u'hidden')
        ce.save()

    return redirect(url_for('.ce_list'))


@bp.route('/scores/refresh')
@require_admin
def refresh_scores():
    d = {
        #        'user': {
        #            'score': 0,
        #            'edit': 0,
        #            'vote': 0,
        #            'punish': 0,
        #            'valid': 0,
        #            'total': 0,
        #        }
    }
    user_logs = {}
    Score.coll().drop()
    for ce in CoreExp.query({'tags': {'$ne': u'hidden'}}):
#        best_option = None
#        if u'closed' in ce.tags:
        best_option = ce.best_option

        for log in ce.get('logs', []):
            user_name = log['user']
            user_logs.setdefault(user_name, [])
            user_logs[user_name].append(log)

        for option in ce.options:
            voters = option['voters']
            for voter in voters:
                d.setdefault(voter, {'score': 0, 'edit': 0, 'vote': 0, 'punish': 0, 'total': 0, 'seconds': 0})
                d[voter]['total'] += 1

            if option['tag'] == u'bad':
                for voter in voters:
                    d[voter]['score'] -= 10
                    d[voter]['punish'] += 1

            if best_option and option['cn'] == best_option['cn']:
                for i, voter in enumerate(voters):
                    if voters[0] != u'SYS' and i < 3:
                        d[voter]['score'] += 5
                        d[voter]['edit'] += 1
                    else:
                        d[voter]['score'] += 1
                        d[voter]['vote'] += 1

#    pprint(user_logs)
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
            seconds = (log['time'] - logs[i-1]['time']).seconds
            if seconds <= 240:
                d[user_name]['seconds'] += seconds
            else:
                print seconds

        score.score = d[user_name]['score']
        score.details = d[user_name]
        score.save()

    return redirect(url_for('.scores'))


@bp.route('/scores')
@require_admin
def scores():
    scores = Score.all({'user': {'$nin': [u'admin', u'SYS']}}, sort=[('score', -1)])
    return render_template('core_exp-scores.html', scores=scores)
