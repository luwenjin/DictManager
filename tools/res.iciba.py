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


def sync_all_pages():

    def fetch_and_store(en, i=None):
        if cb_page_coll.find_one({'en': en}):
            print i, 'skip:', en
            return

        url = 'http://www.iciba.com/%s' % quote(en)
        content = open_url(url)
        doc = pq(content)
        html = unicode(doc('#center'))
        if html:
            page_doc = {
                'en': en,
                'content': html
            }
            cb_page_coll.save(page_doc)
#            print html
            print i, 'saved', en
        else:
            print i, 'empty', en

    for i, token in enumerate(db.Token.find()):
        fetch_and_store(token.en, i)






if __name__ == '__main__':
    sync_all_pages()



