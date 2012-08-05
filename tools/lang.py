#coding:utf-8
'''
语言相关的 工具函数
'''
import re

#pattern_tags = r'[a-zA-Z]+\.'
pattern_POS = (
    ur'(?:\b(?:v|vi|n|conj|adv|adj|ad|a|vt|art|pron|num|prep|int|interj|abbr|aux)\.)'
)
pattern_multi_POSs = pattern_POS+ur'+(?:\uff0f|/|&|,)?'+pattern_POS+u'?'
pattern_meaning_start = r'\(?'+pattern_POS+ur'+(?:\uff0f|/|&|,)?'+pattern_POS+u'?'

def unify_ph(ph):
    ph_map = {

    }


def unify_POS(POS):
    """统一 词性的写法"""
    POS = POS.lower()
    if POS == 'interj.':
        return u'int.'
    if POS == 'adj.':
        return u'a.'
    if POS == 'adv.':
        return u'ad.'
    return POS

def split_POSs(s):
    """将合并在一起的POS分割开"""
    splitter_pattern = ur'\uff0f|/|&|,'
    POSs = re.split(splitter_pattern, s.lower())
    return POSs

def split_by_starts(s, starts):
    starts.append(len(s))
    lines = []
    for i in range(len(starts)-1):
        start = starts[i]
        end = starts[i+1]
        line = s[start:end]
        lines.append(line)
    return lines

def split_meaning_text(s):
    splitter_pattern = ur',\s*|;|，|．|；'
    li = re.split(splitter_pattern, s)
    return li

def split_meaning_spans(meaning_block):
    meaning_block = meaning_block.replace(u'．', '.')
    starts = [x.start() for x in re.finditer(pattern_meaning_start, meaning_block)]
    if starts:
        meaning_lines = split_by_starts(meaning_block, starts)
    else:
        meaning_lines = [meaning_block]
    return meaning_lines

def parse_meaning(line):
    tags = re.findall(pattern_multi_POSs, line)
    if tags:
        tags = tags[0]
        text = line.replace(tags, '')
    else:
        tags = ''
        text = line
    tags = sorted([unify_POS(x) for x in split_POSs(tags)])
    text = text.strip()
    return tags, text

def merge_meanings(parsed_meanings):
    data = {}
    for m in parsed_meanings:
        tags = tuple(m[0])
        text = m[1]
        data.setdefault(tags,set([]))
        data[tags].update(split_meaning_text(text))
    li = []
    for tags in data:
        texts = data[tags]
        if u' ' in texts:
            texts.remove(u' ')
        li.append({
            'POSs': [unicode(x) for x in tags],
            'text': u';'.join(texts),
            })
    return li

def parse_exp(lines):
    """最终的函数， 将纯文字转化为对象"""
    spans = []
    for line in lines:
        spans.extend( split_meaning_spans(line))

    ret = []
    for span in spans:
        meaning = parse_meaning(span)
        ret.append(meaning)

    return ret

def split_cn(cn):
    p = ur'，|；|,|;'

    li = re.split(p, cn)
    li = [x.strip() for x in li]

    ret = []
    for line in li:
        line = purify_cn(line)
        ret.append(line)

    return ret

def purify_cn(cn):
    pl = [
        (u'\(', u'（'),
        (u'\)', u'）'),
        (u'【', u'['),
        (u'】', u']'),
        (ur'（.*）', u''),
        (ur'\[.*\]', u''),
        (ur'\<.*\>', u''),
    ]
    return batch_replace(cn, pl).strip()


def merge_meaning_objects(obj1, obj2):
    meaning_map = {}
#    print obj1+obj2
    for item in obj1+obj2:
        POSs = tuple(item.get("POSs"))
        text = item.get('text')
        meaning_map.setdefault(POSs, set())
        meaning_map[POSs].update(split_meaning_text(text))
    result = []
    for POSs in meaning_map:
        result.append({
            'POSs': list(POSs),
            'text': u';'.join(meaning_map[POSs]),
        })
    return result

def is_phrase(foreign):
    if ' ' in foreign:
        return True
    elif '...' in foreign:
        return True
    else:
        return False

def prepare_data():
    import os
    import sys
    parent_path = os.path.split(os.path.split(__file__)[0])[0]
    print parent_path
    sys.path.append(parent_path)
    #------------------------------------------------------
    from models import Token
    from views._views import get_reference_tokens

    for i, token in enumerate(Token.query(tags=u'word')):
        en = token.en
        print
        print i, en
        refs = get_reference_tokens(en)
        for ref in refs:
            if ref['src'] in ['wn']:
                continue

            lines = ref['exp'].split('<br/>')
            items = parse_exp(lines)
            for item in items:
                cn_li = split_cn(item[1])
                for cn in cn_li:
                    print cn


def batch_replace(line, li):
    for x,y in li:
        line = re.sub(x, y, line)
    return line

def clear_symbols(line):
    symbol_map = {
        u'．': u'.',
        u'；': u';',
        u'，': u',',
        u'。': u',',
    }
    for char_from in symbol_map:
        char_to = symbol_map[char_from]
        line = line.replace(char_from, char_to)
    return line


def test():
    import codecs
    for line in codecs.open('data/cn_samples.txt', encoding='utf-8'):
        line = line.strip()
        print line

        line = clear_symbols(line)
        tp = parse_meaning(line)

        print tp[0], tp[1]
        print


if __name__ == '__main__':
    prepare_data()