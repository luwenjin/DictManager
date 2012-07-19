import os
import re
import sys
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
import requests

sys.path.append(os.path.abspath('../..'))
from models import db, tokens, Token, gt_token_coll
#coll = db['resource.google_translate']

DATA_PATH = 'data/google_translate/tokens.yaml'

def import_into_db():
    pass


def export_tokens():
    li = []
    for en in tokens.distinct('en'):
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
    url = 'http://translate.google.cn/translate_a/t?client=t&text=%s&hl=en&sl=en&tl=zh-CN&ie=UTF-8&oe=UTF-8&multires=1&otf=1&ssel=0&tsel=0&sc=1'
    content = requests.get(url % en).content
    cn = re.findall('\"(.*?)\"', content)
    if cn:
        cn = cn[0]
    return cn


def update_tokens():
    li = load_data()
    update_count = 0
    for doc in li:
        if doc.get('cn'):
            continue
        update_count += 1
        if update_count % 100 == 99:
            dump_data(li)
        en = doc.get('en')
        cn = fetch_cn(en)
        doc['cn'] = cn.decode('utf-8')
        print doc.get('en'), '->', doc.get('cn')
    dump_data(li)

def load_into_db():
    li = load_data()
    for doc in li:

        en = doc.get('en')
        cn = doc.get('cn')
        if type(en) == str:
            en = unicode(en)
        if type(cn) == str:
            cn = unicode(cn)
        if en.lower() == cn.lower():
            continue

        token = gt_token_coll.find_one({'en': en})
        if not token:
            token = {
                'en': en,
                'cn': cn
            }
        gt_token_coll.save(token)
        print 'saved', en, cn



if __name__ == '__main__':
#    cn =  fetch_cn('...sexual intercourse')
#    li = load_data()
#    dump_data(li)
#    export_tokens()
    update_tokens()
