# coding: utf-8
from PySide.QtCore import QObject, Slot, QTimer, QUrl
from PySide.QtGui import QApplication
from PySide.QtNetwork import QNetworkRequest
from PySide.QtWebKit import QWebView, QWebSettings, QWebPage
import requests
import sys


def fetch_url(url, headers=None):
    if headers:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5',
            }.update(headers)

    try:
        content = requests.get(
            url,
            headers=headers,
            timeout=10
        ).content
        return content
    except:
        print 'failed, try again ...'
        return fetch_url(url)



class WebKitSpider(QObject):
    def __init__(self, timeout=30):
        super(WebKitSpider, self).__init__()
        self.url = None
        self._timeout = timeout * 1000

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timeout)

        self.app = QApplication(sys.argv)
        self._web = QWebView()
#        self._web.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True )
        self._web.loadStarted.connect(self._load_started)
        self._web.loadProgress.connect(self._load_progress)
        self._web.loadFinished.connect(self._load_finished)

        self._web.page().networkAccessManager().finished.connect(self._response_finished)

    def load(self, url):
        if type(url) not in [str, unicode]:
            raise Exception('url must be str/unicode')
        self.url = url
        self._web.load(QUrl(url))

    def reload(self):
        self._web.reload()

    def _load_started(self):
#        print 'load_started', self._web.url().toString()
        self.timer.start(self._timeout)

    def _load_progress(self, progress):
#        print 'progress', progress, self._web.url().toString()
        if self.mainFrame.evaluateJavaScript('!window._wsk && (document.getElementsByTagName("head").length>0 ||document.getElementsByTagName("body").length>0) && location.href == "%s" ' % QUrl(self.url).toString()):
#            print 'injected'
            self.mainFrame.addToJavaScriptWindowObject('_wsk', self)
            self.mainFrame.evaluateJavaScript('document.addEventListener("DOMContentLoaded", function(){document.removeEventListener("DOMContentLoaded", arguments.callee, false);window._wsk.ready()})')

    def _load_finished(self):
#        print 'load_finished', self._web.url().toString()
        pass

    def _response_finished(self, reply):
        if reply.url() == self._web.url():
            status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if status_code >= 400:
                self.http_error(status_code)

    def _on_timeout(self):
        self.timeout()

    @property
    def mainFrame(self):
        return self._web.page().mainFrame()

    @Slot()
    def ready(self):
#        print 'call ready from page'
        self.page_ready()

    def run(self):
        self._web.show()
        self.begin()
        sys.exit(self.app.exec_())

    def begin(self):
        pass

    def page_ready(self):
        pass

    def http_error(self, status_code):
        pass

    def timeout(self):
        pass


if __name__ == '__main__':
    class Spider(WebKitSpider):
        def init(self):
            self.load('http://www.iciba.com/hello')

        def page_ready(self):
            print '-------ready'
            self.reload()

    spider = Spider()
    spider.run()
