# coding: utf-8
""" import frequency data """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
import math
import re

from models import db, freq_coll, Token, tokens


def export_freq_data():
    """填充常见程度，来源主要有2个，google ngram / colins"""
    query = {'type': u'word'}

    ng_coll = db['resource.ngram.1']
    ng_coll.ensure_index('lemmas')
    cl_coll = db['resource.collins.tokens']
    cl_coll.ensure_index('en')

    f = open('data/commonness.txt', 'w+')

    for token in db.Token.find():
        en = token.en
        ng = ng_coll.find_one({'lemmas':en})
        if not ng:
            ng = {}
        cl = cl_coll.find_one({'en': en})
        if not cl:
            cl = {}
        line = '%s\t%s\t%s\n'%(en, ng.get('count'), cl.get('current'))
        f.write(line.encode('utf-8'))
        try:
            print line,
        except:
            pass
    f.close()


def calc_freq(freq_doc):
    min_max_logs = {
        'cl_hits': [0, 7.431485639],
        'cl_current': [-6.211478113 , 0.748852145],
        'gn_count': [1.806179974, 9.456220367],
        }
    for key in ['cl_hits', 'cl_current', 'gn_count']:
        if freq_doc.has_key(key) and freq_doc[key] > 0:
            val = freq_doc.get(key)
            min_val, max_val = min_max_logs[key]
            log_val = math.log10(val)
            norm_val = (log_val-min_val)/(max_val-min_val)

            if key == 'cl_hits':
                return norm_val if norm_val else -1
            elif key == 'gn_count':
                return 0.006 + 0.972 * norm_val
            elif key == 'cl_current':
                return 0.011 + 0.969 * (0.006 + 0.972 * norm_val)
            else:
                raise Exception('invalid_key')
    return -1


def guess_freq(phrase):
    special_words = {
        'sb.': 0.5,
        'sb': 0.5,
        'sth.': 0.5,
        'sth': 0.5,
        'oneself': 0.5,
        '...': 0.7
    }

    punctuations = ['!', '.', '?', ',', "'"]

    phrase = re.sub('\(.*?\)', '', phrase)
    phrase = phrase.replace('...', ' ... ')

    freqs = []
    words = phrase.split()
    for word in phrase.split():
        # numbers
        if re.match('\d+', word):
            continue

        # punctuations
        if word in punctuations:
            continue
        if not special_words.has_key(word) and word[-1] in punctuations:
            word = word[:-1]

        # eg: it's up to you
        word = word.replace("'s", '')

        freq_doc = freq_coll.find_one({'en': word})
        if not freq_doc and word != word.lower():
            freq_doc = freq_coll.find_one({'en': word.lower()})

        if freq_doc:
            freqs.append(calc_freq(freq_doc))
        elif special_words.has_key(word):
            freqs.append(special_words[word])
        else:
            print '!!!', word, ':', phrase
            return -1

    ret = 1
    for freq in freqs:
        ret *= freq
    return ret


def fill_all_freqs():
    query = {'freq':-1}
    for i, token in enumerate(db.Token.find(query)):
        en = token.en
        freq_doc = freq_coll.find_one({'en': en})

        if freq_doc:
            freq = calc_freq(freq_doc)
        if freq <= 0:
            freq = guess_freq(en)

        print en, freq, token.courses
        if freq > 0:
            token.freq = freq
            token.save()

    print 'left:', tokens.find({'freq': -1}).count()


if __name__ == '__main__':
    fill_all_freqs()