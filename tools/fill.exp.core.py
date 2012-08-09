# coding: utf-8
""" import exp.core """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
from collections import Counter

from models import db
from views._views import get_reference_tokens
from lang import parse_exp, split_cn




def fill_auto_coreexp():
    for i, token in enumerate(db.Token.find()):
        if token.core.exp:
            continue

        en = token.en

        counter = Counter()
        refs = get_reference_tokens(token.en)
        for ref in refs:
            if ref['src'] in ['wn']:
                continue

            lines = ref['exp'].split('<br/>')
            items = parse_exp(lines)

            for item in items:
                cn_li = split_cn(item[1])
                for cn in cn_li:
                    if cn:
                        counter[cn] += 1

        for cn, count in counter.most_common(1):
            tpl = (
                '%(total)s\n'
                '%(others)s'
                )

            total = sum(counter.values())
            score = 1.0 * count / total
            others = []
            for j, (s, n) in enumerate(counter.most_common()):
                others.append((s,n))
            others = ','.join([ '%s[%s]' % x for x in others ])
            d = {
                'en': en,
                'cn': cn,
                'count': count,
                'total': total,
                'score': score,
                'others': others
            }
            note = tpl % d

            token.exp.core = cn
            token.note = note
            token.save()
            print i, en, cn


if __name__ == '__main__':
    fill_auto_coreexp()