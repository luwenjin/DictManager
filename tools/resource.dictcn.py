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

from models import db, tokens, dc_page_coll, dc_token_coll, Token



def save_pages():
    dc_page_coll.ensure_index('en')
    ghost = Ghost(cache_dir='d:/temp')
    for i, token in enumerate(Token.query()):
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




def parse_page(html):
    d = pq(html)
    doc = dict()
    # en
    doc['en'] = d('#word-key').text()

    #phonetics
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
    doc['ph_en'] = ph_en
    doc['ph_us'] = ph_us

    # exps : {POS:, cn:}
    p_li = d('div.shiyi p')
    for p in p_li:
        p = pq(p)
        POS = p('strong').text()
        cn = p.text().replace(POS, '').strip()
        doc.setdefault('exps', [])
        doc['exps'].append({'POS': POS, 'cn': cn})

    pprint(doc)








if __name__ == '__main__':
#    init_pages_collection()
#    dc_token_coll.drop()
#    update_tokens()
#    dc_page_coll.drop()
#    doc = dc_page_coll.find_one()
#    parse_page(doc['content'])
#    save_pages()
    db['core_exp'].drop()
    db['users'].drop()
