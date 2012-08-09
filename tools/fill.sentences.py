# coding: utf-8
""" import all kinds of resources into main db """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
import math
import re

from collections import Counter


from models import db, qj_course_coll, qj_token_coll, qj_sentence_coll, \
    dc_token_coll, yd_simple_token_coll, freq_coll
from models import Token, tokens, Sentence
from views._views import get_reference_tokens
from lang import parse_exp, split_cn




def fill_auto_coreexp():
    for i, token in enumerate(Token.query()):
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




def update_qj_sentences():
    # todo
    pass




if __name__ == '__main__':
    fill_all_freqs()



