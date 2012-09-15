#coding:utf-8
import sys
import os
from pprint import pprint
from PySide.QtCore import QTimer, SLOT, QUrl

parent_path = os.path.split(os.path.split(__file__)[0])[0]
print 'parent_path:', parent_path
sys.path.append(parent_path)
#------------------------------------------------------
import re
from urllib import quote

from pyquery import PyQuery as pq
import workerpool
from bson import Binary
import zlib

from models import cb_page_coll, db
from utils import fetch_url, WebKitSpider

class ICibaSpider(WebKitSpider):
    def begin(self):
        self.total = cb_page_coll.find({'zip':{'$exists': False}}).count()
        self.count = 0
        self.en = None
        self.html = None
        self.crawl_next()

    def page_ready(self):
        QTimer.singleShot(100, self, SLOT('crawl_next()'))

    def http_error(self):
        print 'http_error'
        QTimer.singleShot(100, self, SLOT('reload()'))

    def timeout(self):
        print 'timeout'
        QTimer.singleShot(100, self, SLOT('reload()'))

    def crawl_next(self):
        if self.en:
            page = cb_page_coll.find_one({'en': self.en})
            if page:
                content = self.mainFrame.toHtml()
                page['zip'] = Binary(zlib.compress(content.encode('utf-8')))
                cb_page_coll.save(page)
                self.count += 1
                print 'saved', len(content), self.en
                print '--------------------------------------'

        page = cb_page_coll.find_one({'zip':{'$exists': False}})
        if not page:
            sys.exit()
        else:
            self.en = page['en']
            url = 'http://www.iciba.com/%s' % quote(self.en, safe="'")
            print 'crawl_next', self.count, '/', self.total, self.en
            self.load(url)



def sync_ens():
    cb_page_coll.ensure_index('en')
    for i, token in enumerate(db.Token.find()):
        if cb_page_coll.find_one({'en': token.en}):
            continue
        print i, token.en
        cb_page_coll.save({'en':token.en})


def sync_all_pages():
    cb_page_coll.ensure_index('en')
    spider = ICibaSpider(30)
    spider.run()


def parse_page(html):
    d = pq(html)
    ret = dict()
    ret['en'] = d('h1').text()
    return ret


def fix_page_crawl():
    for page in cb_page_coll.find({'zip':{'$exists': True}}):
        try:
            bin = page['zip']
            html = zlib.decompress(bin)
            doc = parse_page(html)
            if doc.get('en') and doc['en'].lower() != page['en'].lower():
                print page['en'], doc['en']
                doc.pop('zip')
                cb_page_coll.save(page)
        except:
            doc.pop('zip')
            cb_page_coll.save(page)

def zip_all_pages():
    for i, page in enumerate(cb_page_coll.find({'content':{'$ne': u''}})):
        content = page['content'].encode('utf-8')
        content = zlib.compress(content)
        page['zip'] = Binary(content)
        page.pop('content')
        cb_page_coll.save(page)
        print i, page['en']


if __name__ == '__main__':
#    cb_page_coll.drop()
#    sync_ens()

    sync_all_pages()

#    fix_page_crawl()




