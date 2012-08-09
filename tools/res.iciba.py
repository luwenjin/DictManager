#coding:utf-8
import sys
import os
from pprint import pprint
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
import re
from urllib import quote

from ghost import Ghost
from pyquery import PyQuery as pq

from models import dc_page_coll, db



def sync_all_pages():
    dc_page_coll.ensure_index('en')
    ghost = Ghost(cache_dir='d:/temp')
    for i, token in enumerate(db.Token.find()):
        en = token.en
        page_doc = dc_page_coll.find_one({'en': en})
        if not page_doc:
            url = 'http://dict.cn/%s' % quote(en)
            try:
                ghost.open(url)
            except:
                ghost.open(url)
            content = ghost.content
            doc = pq(content)
            html = unicode(doc('#cy'))
            page_doc = {
                'en': en,
                'content': html
            }
            dc_page_coll.save(page_doc)
            print html
            print i, 'saved', en
        else:
            print i, 'skipped', en


def parse_en(d):
    return d('#word-key').text()


def parse_phs(d):
    texts = d('.yinbiao').text()
    p = re.compile('\[(.*?)\]')
    li = p.findall(texts)
    ph_en, ph_us = None, None
    if len(li) == 2:
        ph_en, ph_us = li
    elif len(li) == 1:
        if u'英' in texts:
            ph_en = li[0]
        else:
            ph_us = li[0]
    return {
        'ph_en': ph_en,
        'ph_us': ph_us
    }


def parse_exp(d):
    ret = {'exps': []}
    p_li = d('div.shiyi p')
    for p in p_li:
        p = pq(p)
        POS = p('strong').text()
        cn = p.text().replace(POS, '').strip()
        ret['exps'].append({'POS': POS, 'cn': cn})
    return ret



def parse_page(html):
    d = pq(html)
    doc = dict()

    doc['en'] = parse_en(d)
    doc.update(parse_phs(d))
    doc.update(parse_exp(d))

#    print 'en\t', doc['en']
#    print 'ph_en\t', doc['ph_en']
#    print 'ph_us\t', doc['ph_us']
#    print


def parse_all_pages():
    for page in dc_page_coll.find():
        print page['en']
        if page['content']:
            try:
                doc = parse_page(page['content'])
            except:
                dc_page_coll.remove(page)
        else:
            pass
#            dc_page_coll.remove(page)
#            print '!!! error page delete', page['en']



if __name__ == '__main__':
    dc_page_coll.remove({'en': u"o'clock"})
#    sync_all_pages()



