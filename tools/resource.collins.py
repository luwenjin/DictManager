#coding:utf-8
import sys
import os
import urllib
import time
from pprint import pprint
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
from models import db, tokens, cl_token_coll, cl_page_coll, cl_freq_page_coll

from pymongo.objectid import ObjectId
from pyquery import PyQuery as pq
import requests
import json

def get_commonness_info(en):
    encoded_en = urllib.quote(en.encode('utf-8'))
    url = 'http://www.collinsdictionary.com/corpus/english/current/' + encoded_en
    try:
        content = requests.get(url).content
    except:
        print 'sleep...'
        time.sleep(10)
        return get_commonness_info(en)
    try:
        info = json.loads(content)
    except:
        print 'sleep...'
        time.sleep(10)
        return get_commonness_info(en)
    return info

def get_freq_info(en):
    encoded_en = urllib.quote(en.encode('utf-8'))
    url = 'http://wordbanks.harpercollins.co.uk/auth/corpora/run.cgi/first?corpname=preloaded%2Fwbo-english.conf&iquery='+encoded_en+'&lemma=&lpos=&phrase=&word=&wpos=&cql=&default_attr=word&fctxtype=all&fclwsize=5&fcrwsize=5&fcllemma=&fcrlemma=&sca_doc.year=&sca_doc.titl='
    try:
        content = requests.get(
            url,
            headers={
                'Cookie': 'showhidden=rect_url="./?".keywordel; login_redirect_url="./?1331221295"; 1331221295|3672069|19430|0|0|0=1331221295%7C3672069%7C19430%7C0%7C0%7C0; __utma=39153829.670017239.1330633252.1330633252.1330633252.1; __utmc=39153829; __utmz=39153829.1330633252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); login_redirect_url="./?"; um_session=mrCred3vBpxKDPAV6nR764Em9; 1331221295|3672069|19430|0|0|0=1331221295%7C3672069%7C19430%7C0%7C0%7C0; __utma=39153829.670017239.1330633252.1330633252.1330633252.1; __utmb=39153829.1.10.1331221725; __utmc=39153829; __utmz=39153829.1330633252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)'
            },
            timeout=20
        ).content
    except:
        print 'failed, try again...'
        return get_freq_info(en)
    return content


def crawl_freq_pages():
    cl_freq_page_coll.ensure_index('en')
    for i, page in enumerate(cl_freq_page_coll.Page.find()):
        if '<input type="text" name="user" /' in page.content:
            page.delete()
            print i, 'del', page.en
    cursor = tokens.Token.find({
        'is_trash': False,
        'is_phrase': False,
#        'courses': {'$in': ['CET4', 'CET6', 'GRE', 'TOEFL', "TOEIC"]}
    })
    count = cursor.count()
    for i, token in enumerate(list(cursor)):
        en = token.en
        freq_page = cl_freq_page_coll.Page.find_one({'en': en})
        print i, '/', count, token.en,
        if freq_page:
            print 'skip'
            continue
        try:
            content = get_freq_info(en)
            d = pq(content)
            table = d('table').eq(0)
            hits = pq('b', table).eq(1).text()
        except:
            print 'failed'
            return
        freq_page = cl_freq_page_coll.Page()
        freq_page.en = en
        freq_page.content = content
#        if i%10 == 0:
#            print content
        freq_page.save()
        print 'saved', hits


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
            info = get_commonness_info(en)
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

def get_page(en):
    en = en.encode('utf-8')
    url = 'http://www.collinsdictionary.com/dictionary/english/' + urllib.quote(en)
    try:
        content = requests.get(url).content
    except:
        print 'sleep...'
        time.sleep(10)
        return get_page(en)
    if type(content) == str:
        print 'sleep...'
        time.sleep(30)
        return get_page(en)
    return content

def update_pages():
    cl_page_coll.ensure_index('en')
    en_list = tokens.find({'is_phrase': False}).distinct('en')
    for i, en in enumerate(en_list):
        cl_page = cl_page_coll.CLPageq.find_one({'en': en})
        if cl_page:
            print i, 'skip', en
        else:
            content = get_page(en)
            cl_page = cl_page_coll.CLPage()
            cl_page.en = en
            cl_page.content = content
            cl_page.save()
            print i, 'saved', en
            if i%100 == 1: print content




if __name__ == '__main__':
    crawl_freq_pages()
#    update_commonness()
#    update_pages()