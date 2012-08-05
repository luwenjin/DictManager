import os
import re
import sys
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
import requests

sys.path.append(os.path.abspath('../..'))
from models import tokens, gt_token_coll
#coll = db['resource.google_translate']

DATA_PATH = 'data/google_translate/tokens.yaml'


def export_tokens():
    li = load_data()
    mp = {}
    for i, item in enumerate(li):
        en = item['en']
        if re.findall('s\.?b\.?', en) or re.findall('sth\.?', en):
            continue

        mp[en] = item
    li = mp.values()
    for en in tokens.distinct('en'):
        if mp.has_key(en):
            continue
        else:
            doc = {
                'en': en.encode('utf8'),
                'cn': ''
            }
            li.append(doc)
    dump_data(li)


def dump_data(data):
    print 'dumping...',
    yaml.dump(data, open(DATA_PATH, 'w+'), Dumper=Dumper, default_flow_style=False, encoding='utf-8',
        allow_unicode=True)
    print 'done'


def load_data():
    print 'loading...',
    data = yaml.load(open(DATA_PATH), Loader=Loader)
    print 'done'
    return data


def fetch_cn(en):
    en = en.replace('sb.', 'somebody')
    en = en.replace('sth.', 'something')
    url = 'http://translate.google.cn/translate_a/t?client=t&text=%s&hl=en&sl=en&tl=zh-CN&ie=UTF-8&oe=UTF-8&multires=1&otf=1&ssel=0&tsel=0&sc=1'
    content = requests.get(url % en).content
#    print content
    cn = re.findall('\"(.*?)\"', content)
    if cn:
        cn = cn[0]
    return content


def update_tokens():
    li = load_data()
    update_count = 0
    total_count = len(li)
    for i, doc in enumerate(li):
        if doc.get('cn'):
            continue
        update_count += 1
        if update_count % 100 == 99:
            dump_data(li)
        en = doc.get('en')
        cn = fetch_cn(en)
        doc['cn'] = cn.decode('utf-8')
        print i, '/', total_count, doc.get('en'), '->', doc.get('cn')
    dump_data(li)


def save_all():
    gt_token_coll.drop()
    gt_token_coll.ensure_index('en')
    li = load_data()
    for i, item in enumerate(li):
        en = item.get('en')
        cn = item.get('cn')

        doc = parse_gt(cn)

        token = gt_token_coll.find_one({'en': en})
        if not token:
            gt_token_coll.save(doc)
            print i, 'saved', en, doc


def parse_gt(s):
    while ',,' in s:
        s = s.replace(',,', ',None,')
    li = eval(s)
    base_li, pos_li, _, _, l3, l4, _, _, _, _ = li

    base_li = base_li[0]
    cn, en, py, _ = base_li

    doc = {
        'en': en.decode('utf-8'),
        'py': py.decode('utf-8')
    }

    doc['poss'] = {}
    if pos_li:
        for li in pos_li:
            pos, cn_li, _ = li
            doc['poss'][pos] = [cn.decode('utf-8') for cn in cn_li]

    if len(l3) == 1:
        for li in l4:
            if li[-1] == doc['en']:
                doc['cns'] = [x[0] for x in li[2]]
    else:
        doc['cns'] = [cn]

    doc['cns'] = [cn.decode('utf-8') for cn in doc['cns']]

    return doc







if __name__ == '__main__':
    save_all()

