#coding:utf-8
import sys
import os
from pprint import pprint
from PySide.QtCore import QUrl, QObject, Slot, QTimer, SLOT
from PySide.QtGui import QApplication
from PySide.QtWebKit import QWebView, QWebSettings
from PySide.QtNetwork import QNetworkRequest

parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
import re
from urllib import quote

from pyquery import PyQuery as pq
import workerpool
from bson import Binary
import zlib

from models import dc_page_coll, db
from utils import WebKitSpider


def sync_ens():
    dc_page_coll.ensure_index('en')
    for i, token in enumerate(db.Token.find()):
        if dc_page_coll.find_one({'en': token.en}):
            continue
        dc_page_coll.save({
            'en': token.en,
            'content': u''
        })
        print 'insert', i, token.en



class DCSpider(WebKitSpider):
    def begin(self):
        self.total = dc_page_coll.find({'zip':{'$exists': False}}).count()
        self.count = 0
        self.en = None
        self.crawl_next()

    def page_ready(self):
        QTimer.singleShot(100, self, SLOT('crawl_next()'))

    def crawl_next(self):
        if self.en:
            page = dc_page_coll.find_one({'en': self.en})
            if page:
                content = self.mainFrame.toHtml()
                page['zip'] = Binary(zlib.compress(content.encode('utf-8')))
                dc_page_coll.save(page)
                self.count += 1
                print 'saved', len(content), self.en
                print '--------------------------------------'

        page = dc_page_coll.find_one({'zip':{'$exists': False}})
        if not page:
            sys.exit()
        else:
            self.en = page['en']
            print self.en
            url = 'http://dict.cn/%s' % quote(self.en.encode('utf-8'), safe="'!")
            self.load(url)
            print 'crawl_next', self.count, '/', self.total, self.en

    def timeout(self):
        QTimer.singleShot(100, self, SLOT('reload()'))

    def http_error(self, status_code):
        print 'http_error', status_code
        if status_code != 404:
            QTimer.singleShot(100, self, SLOT('reload()'))


def sync_all_pages():
    dc_page_coll.ensure_index('en')

    spider = DCSpider()
    spider.run()


def parse_page(html):
    ret = {}

    d = pq(html)
    if d('title').text() == u'404页面':
        return ret

    ret['en'] = d('h1.keyword').text()

    ph_spans = d('div.phonetic span')
    if ph_spans:
        span_ph_en, span_ph_us = ph_spans
        ret['ph'] = {
            'en': pq('bdo', span_ph_en).text(),
            'us': pq('bdo', span_ph_us).text()
        }

    ret['exp'] = {'basic':[]}
    for li in d('div.section.def .basic ul li'):
        pos = pq('span', li).text()
        cn = pq('strong', li).text()
        ret['exp']['basic'].append({
            'pos': pos,
            'def': cn
        })

    ret['sentences'] = []
    sent_lis = d('div.section.sent .sort ul li')
    for li in sent_lis:
        en_html, cn_html = pq(li).html().split('<br />')
        en = pq(en_html).text()
        cn = pq(cn_html).text()
        ret['sentences'].append({
            'en': en,
            'cn': cn
        })

    return ret


def fix_page_crawl():
    for page in dc_page_coll.find({'zip':{'$exists': True}}):
        try:
            bin = page['zip']
            html = zlib.decompress(bin)
            doc = parse_page(html)
            if doc.get('en') and doc['en'].lower() != page['en'].lower():
                print page['en'], doc['en']
                doc.pop('zip')
                dc_page_coll.save(page)
        except:
            doc.pop('zip')
            dc_page_coll.save(page)

def zip_all_pages():
    for i, page in enumerate(dc_page_coll.find({'content':{'$ne': u''}})):
        content = page['content'].encode('utf-8')
        content = zlib.compress(content)
        page['zip'] = Binary(content)
        page.pop('content')
        dc_page_coll.save(page)
        print i, page['en']



if __name__ == '__main__':
#    dc_page_coll.drop()
#    sync_ens()

#    zip_all_pages()
    sync_all_pages()

#    fix_page_crawl()


