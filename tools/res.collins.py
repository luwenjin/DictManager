#coding:utf-8
import sys
import os
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
sys.path.append(parent_path)
#------------------------------------------------------
import json
import urllib
import time

from bson.objectid import ObjectId
from pyquery import PyQuery as pq
import requests
import workerpool

from models import db, Token, tokens, cl_token_coll, cl_page_coll, cl_freq_page_coll


def fetch_commonness_info(en):
    """seems 404ed"""
    encoded_en = urllib.quote(en.encode('utf-8'))
    url = 'http://www.collinsdictionary.com/corpus/english/current/' + encoded_en
    try:
        content = requests.get(url).content
    except:
        print 'sleep...'
        time.sleep(10)
        return fetch_commonness_info(en)
    try:
        info = json.loads(content)
    except:
        print 'sleep...'
        time.sleep(10)
        return fetch_commonness_info(en)
    return info


def fetch_hits_page(en):
    """ http://wordbanks.harpercollins.co.uk/auth/
    Username    : f5dev543
    Password    : DyF2LXxo
    """
    encoded_en = urllib.quote(en.encode('utf-8'))
    url = 'http://wordbanks.harpercollins.co.uk/auth/corpora/run.cgi/first?corpname=preloaded%2Fwbo-english.conf&iquery='+encoded_en+'&lemma=&lpos=&phrase=&word=&wpos=&cql=&default_attr=word&fctxtype=all&fclwsize=5&fcrwsize=5&fcllemma=&fcrlemma=&sca_doc.year=&sca_doc.titl='
    try:
        content = requests.get(
            url,
            headers={
                'Cookie': 'login_redirect_url="./?"; login_redirect_url="./?"; um_session=DgSbWaocAhfq7PZqfxFng4ZXx; __utma=39153829.278053318.1344092391.1344092391.1344092391.1; __utmb=39153829.1.10.1344092391; __utmc=39153829; __utmz=39153829.1344092391.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
                'Referer': 'http://wordbanks.harpercollins.co.uk/auth/corpora/run.cgi/first_form?corpname=preloaded/wbo-english.conf',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5',
            },
            timeout=20
        ).content
        return content
    except:
        print 'failed, try again...'
        return fetch_hits_page(en)


def fetch_dict_page(en):
    en = en.encode('utf-8')
    url = 'http://www.collinsdictionary.com/dictionary/english/' + urllib.quote(en)
    content = requests.get(url).content
    return content


def sync_all_hits_pages():
    cl_freq_page_coll.ensure_index('en')

    cursor = Token.query() #maybe: {'freq': -1}
    count = cursor.count()

    en_list = []
    i_list = []
    for i, token in enumerate(cursor):
        i_list.append(i)
        en_list.append(token.en)

    def fetch_and_store(en, i):
        freq_page = cl_freq_page_coll.find_one({'en': en})
        if freq_page and '<input type="text" name="user" /' in freq_page['content']:
            cl_freq_page_coll.remove(freq_page)
            freq_page = None

        if freq_page:
            print i, '/', count, en, 'skip'
            return

        content = None
        try:
            content = fetch_hits_page(en)
            d = pq(content)
            table = d('table').eq(0)
            hits = pq('b', table).eq(1).text()
        except:
            print i, '/', count, en, 'failed'
            print content
            return

        freq_page = {
            'en': en,
            'content': content
        }

        cl_freq_page_coll.save(freq_page)
        print i, '/', count, en, 'saved', hits

    pool = workerpool.WorkerPool(size=5)
    pool.map(fetch_and_store, en_list, i_list)

    pool.shutdown()
    pool.wait()


def fill_en_from_tokens():
    for token in tokens.find():
        en = token['en']
        cl_token = cl_token_coll.find_one({'en': en})
        if not cl_token:
            cl_token = {'en': en}
            cl_token_coll.save(cl_token)
            print 'add', en


def fill_hits_from_freq_pages():
    for i, cl_token in enumerate(cl_token_coll.find()):
        en = cl_token['en']

        freq_page_doc = cl_freq_page_coll.find_one({'en': en})
        if freq_page_doc:
            d = pq(freq_page_doc['content'])
            table = d('table').eq(0)
            hits = pq('b', table).eq(1).text()

            if hits:
                try:
                    hits = int(hits)
                    cl_token['hits'] = hits
                    cl_token_coll.save(cl_token)
                    print i, en, hits
                except:
                    print '!!!!', i, en, hits


def fill_band_from_pages():
    for i, cl_page in enumerate(cl_page_coll.find()):
        en = cl_page['en']

        d = pq(cl_page['content'])

        title = d('#usage_level').attr('title')
        if title:
            li = title.split('"')
            if li:
                band = int(li[1].strip())
                print en, band





def update_commonness():
    cl_token_coll.ensure_index('en')

    en_list = tokens.find({'is_phrase': False}).distinct('en')
    for i, en in enumerate(en_list):
        if i<0:
            continue
        cl_token = cl_token_coll.CLToken.find_one({'en': en})
#        print cl_token
        if cl_token and cl_token.current:
            print i, 'skip', en
        else:
            print en,
            info = fetch_commonness_info(en)
            print info
            cl_token = cl_token_coll.CLToken()
            if type(info) == dict and info.get('band'):
                cl_token.current = info.get('current')
                cl_token.band = info.get('info')
                cl_token.en = en
                cl_token.save()
                print i, 'saved', en
            elif type(info) == list:
                cl_token.current = -1.0
                cl_token.band = -1
                cl_token.en = en
                cl_token.save()





def update_pages():
    cl_page_coll.ensure_index('en')

    en_list = tokens.find().distinct('en')


    def fetch_and_store_page(en, i=None):
        print i, en
        content = fetch_dict_page(en)
        print content
        cl_page = cl_page_coll.find_one({'en': en})
        if not cl_page:
            cl_page = {}
        cl_page['en'] = en
        cl_page['content'] = content
        cl_page_coll.save(cl_page)


#    fetch_and_store_page(en_list[0])

    pool = workerpool.WorkerPool(size=3)
    pool.map(fetch_and_store_page, en_list, range(len(en_list)))

    pool.shutdown()
    pool.wait()



if __name__ == '__main__':
#    crawl_freq_pages()
#    ens = cl_token_coll.distinct('en')
#    for en in ens:
#        tokens = list(cl_token_coll.find({'en': en}))
#        if len(tokens)>1:
#            cl_token_coll.remove(tokens[1])
#            print 'removed'
    fill_en_from_tokens()
