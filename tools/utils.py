# coding: utf-8
import requests
from ghost import Ghost


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


ghost = Ghost(cache_dir='d:/temp')
def open_url(url):
    try:
        ghost.open(url)
        content = ghost.content
        return content
    except:
        print 'failed, try again ...'
        return open_url(url)