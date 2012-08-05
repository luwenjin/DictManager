# coding: utf-8
import os
import random
from collections import Counter

from models import CoreExp, gt_token_coll, Token
from views._views import get_reference_tokens
from tools.lang import parse_exp, split_cn


def repair_anti_spam():
    spam_users = [
        '55641641',
        '54664523',
        '3032996+363',
        '94691312',
        '46546514',
        '78854',
        '565654',
        '456789',
        '79413',
        '94646346',
        'villa',
        '85494+8',
        'twity',
        '88866',
        '894++++',
        'twitygood',
        ]

    for user_name in spam_users:
        for ce in CoreExp.query({
            'tags': {'$ne': u'hidden'},
            'actions_count': {'$gt': 0},
            'options.voters': user_name}
        ):
            for option in ce.options:
                if user_name in option['voters']:
                    option['voters'].remove(user_name)
                    print ce.en, 'removed', user_name
            ce.save()

def stat_time_cost_distribution():
    user_logs = {}
    user_times = {}
    for ce in CoreExp.query({'tags': {'$ne': u'hidden'}}):
        for log in ce.logs:
            user_name = log['user']
            user_logs.setdefault(user_name, [])
            user_logs[user_name].append(log)

    for user_name in user_logs:
        logs = user_logs[user_name]
        logs.sort(key=lambda x:x.get('time'))

        user_times.setdefault(user_name, [])
        for i, log in enumerate(logs):
            seconds = (log['time'] - logs[i-1]['time']).seconds
            if seconds <= 240:
                user_times[user_name].append(seconds)
            else:
                user_times[user_name].append(0)

    for i in range(300):
        t_li = []
        for user_name in user_times:
            logs = user_logs[user_name]
            if len(logs) <300:
                break
            else:
                t_li.append(user_times[user_name][i])
        print '%s\t%0.2f' % (i, 1.0*sum(t_li) / len(t_li))


def fill_coreexp_task(course_name, filled_amount):
    old_amount = CoreExp.query().count()
    new_amount = filled_amount - old_amount

    if new_amount <= 0:
        return

    valid_tokens = Token.all(courses=course_name)
    token_map = {}
    for token in valid_tokens:
        token_map[token.en] = token
    for ce in CoreExp.query():
        if token_map.has_key(ce.en):
            token_map.pop(ce.en)
    valid_tokens = token_map.values()

    for i in xrange(new_amount):
        n = random.randint(0, len(valid_tokens)-1)
        token = valid_tokens[n]
        del valid_tokens[n]

        gt_token = gt_token_coll.find_one({'en': token.en})
        ce = CoreExp.one(en=token.en)
        if gt_token and not ce:
            ce = CoreExp.new()
            ce.en = token.en
            for cn in gt_token['cns']:
                ce.options.append({
                    'cn': cn,
                    'voters': [u'SYS'],
                    'tag': None
                })

            if gt_token['cns']:
                ce.save()
            print ce.en

        if len(valid_tokens) <= 0:
            break

def auto_ce():
    f = open('tools/data/cn_samples/all.txt', 'w+')
    for i, token in enumerate(Token.query({
        'courses':u'IELTS',
#        'exp.core': u'',
    })):
        # kill idiot meaning
#        new_options = []
#        for option in ce.options:
#            if option['cn'] and option['cn'][0] == u'的':
#                print ce.en, option['cn']
#            else:
#                new_options.append(option)
#        if new_options:
#            ce.options = new_options
#            ce.save()

        # add references

        counter = Counter()
        refs = get_reference_tokens(token.en)
        for ref in refs:
            if ref['src'] in ['wn']:
                continue
#                lines = ref['exp'].split('<br/>')
#                if len(lines) == 1:
#                    print token.en,lines[0]

            lines = ref['exp'].split('<br/>')
            items = parse_exp(lines)

            for item in items:
                cn_li = split_cn(item[1])
                for cn in cn_li:
                    if cn:
                        counter[cn] += 1

        for cn, count in counter.most_common(1):
            tpl = (
                '%(en)s\t'
                '%(count)s\t'
                '%(cn)s\t'
                '%(score).2f\t'
                '%(total)f\t'
                '%(others)s\n'
            )

            en = token.en
            total = sum(counter.values())
            score = 1.0 * count / total
            others = []
            for i, (s, n) in enumerate(counter.most_common()):
                others.append((s,n))
            others = '\t'.join([ '%s\t%s' % (x[1],x[0]) for x in others ])
            d = {
                'en': en,
                'cn': cn,
                'count': count,
                'total': total,
                'score': score,
                'others': others
            }


            line = tpl % d
            line = line.encode('utf-8')
            f.write(line)

            print cn, count







    # add references



if __name__ == '__main__':
    auto_ce()