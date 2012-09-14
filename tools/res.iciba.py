#coding:utf-8
import sys
import os
from pprint import pprint
parent_path = os.path.split(os.path.split(__file__)[0])[0]
print 'parent_path:', parent_path
sys.path.append(parent_path)
#------------------------------------------------------
import re
from urllib import quote

from pyquery import PyQuery as pq
import workerpool

from models import cb_page_coll, db
from utils import fetch_url, open_url


def fill_tokens_en():
    for i, token in enumerate(db.Token.find()):
        if cb_page_coll.find_one({'en': token.en}):
            continue
        print i, token.en
        cb_page_coll.save({'en':token.en, 'content': u''})

def sync_all_pages():
    def fetch_and_store(en, i=None):
        cb_page = cb_page_coll.find_one({'en': en})

        if cb_page and cb_page['content']:
            print i, 'skip:', en
            return
        try:
            url = 'http://www.iciba.com/%s' % quote(en)
        except:
            return
        content = open_url(url)
        doc = pq(content)
        html = unicode(doc('#center'))
        if not cb_page:
            cb_page = {'en': en, 'content': u''}
        if html:
            cb_page['content'] = html
            cb_page_coll.save(cb_page)
#            print html
            print i, 'saved', en
        else:
            print i, 'empty', en

    for i, token in enumerate(db.Token.find()):
        en = token['en']
        fetch_and_store(en, i)


if __name__ == '__main__':
    sync_all_pages()




