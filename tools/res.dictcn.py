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

from models import dc_page_coll, db


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

class WebKitSpider(QObject):
    def __init__(self):
        super(WebKitSpider, self).__init__()
        self._agent_injected = False

        self.app = QApplication(sys.argv)
        self.web = QWebView()
#        self.web.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True )
        self.web.loadStarted.connect(self._load_started)
        self.web.loadProgress.connect(self._load_progress)
        self.web.loadFinished.connect(self._load_finished)

        self.web.page().networkAccessManager().finished.connect(self._response_finished)

        self.init()

    def _load_started(self):
        pass

    def _load_progress(self, progress):
#        print 'progress', progress
        self.mainFrame.evaluateJavaScript(u'''
        if (!window._wks_injected && window.$) {
            window._wks_injected = true;
            document.addEventListener("DOMContentLoaded", function(){
                window._wks.ready();
            }, true);
        }
        ''')
        self.mainFrame.addToJavaScriptWindowObject('_wks', self)

    def _load_finished(self):
        pass

    def _response_finished(self, reply):
        if reply.url() == self.web.url():
            status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if status_code >= 400:
                self.http_error(status_code)

    @property
    def mainFrame(self):
        return self.web.page().mainFrame()

    @Slot()
    def ready(self):
        self.page_ready()


    def start(self):
        self.web.show()
        self.crawl_next()
        sys.exit(self.app.exec_())

    def init(self):
        # to be override
        pass

    def page_ready(self):
        pass

    def crawl_next(self):
        # to be override
        pass

    def http_error(self, status_code):
        # to be override
        pass




class DCSpider(WebKitSpider):
    def init(self):
        self.total = dc_page_coll.find({'content':u''}).count()
        self.count = 0
        self.en = None

    def page_ready(self):
#        self.web.stop()
        QTimer.singleShot(100, self, SLOT('crawl_next()'))

    def crawl_next(self):
        print 'crawl_next', self.en
        if self.en:
            page = dc_page_coll.find_one({'en': self.en})
            if page:
                content = self.mainFrame.toHtml()
                page['content'] = content
                dc_page_coll.save(page)
                self.count += 1
                print 'saved', len(content), self.count, '/', self.total, self.en
                print '--------------------------------------'

        page = dc_page_coll.find_one({'content': u''})
        self.en = page['en']
        url = 'http://dict.cn/%s' % quote(self.en, safe="'")
        self.web.load(QUrl(url))

    def http_error(self, status_code):
        QTimer.singleShot(100, self, SLOT('crawl_next()'))


def fetch_all_pages():
    dc_page_coll.ensure_index('en')

    spider = DCSpider()
    spider.start()


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






if __name__ == '__main__':
#    dc_page_coll.drop()
#    sync_ens()

    fetch_all_pages()

#    for page in dc_page_coll.find({'content':{'$ne':u''}}):
#        html = page['content']
#        ret = parse_page(html)
#        pprint(ret)
#        pass


