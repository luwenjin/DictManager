#coding:utf-8
import sys
import os
from pprint import pprint
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
from models import db, tokens, dc_page_coll, dc_token_coll
from pymongo.objectid import ObjectId
from pyquery import PyQuery as pq

def init_pages_collection():
    dc_page_coll.ensure_index('en')
    for i, token in enumerate(tokens.Token.find()):
        en = token.en
        page = dc_page_coll.DCPage.find_one({'en': token.en})
        if not page:
            page = dc_page_coll.DCPage()
            page.en = en
            page.save()
            print i, 'save', en
        else:
            print i, 'skip', en

def parse_page(html):
    d = pq(html)
    token = d('#word-key').text()

    token_seg = d('#word-key').attr('seg')

    phonetics = None
    phonetic_text = d('div.h2-titles .yinbiao').text()
    if phonetic_text:
        phonetics = [ unicode(x.strip()) for x in phonetic_text.replace('[','').replace(']','').split(';')]

    level = None
    level_text = d('#word-level').attr('level')
    if level_text:
        pos = level_text.index(u'星')
        level = int(level_text[pos-1:pos])

    transforms = {}
    change_li = d('#word-transform a')
    for change_el in change_li:
        desc = pq(change_el).attr('desc')
        foreign = pq(change_el).text()
        transforms[desc] = unicode(foreign)

    explains = []
    current_explain = None
    for node in d('#exp-block li,#exp-block div.exp'):
        if node.tag == 'li':
            current_explain = pq(node).text()
            explains.append({
                'exp': unicode(current_explain),
                'sentences': []
            })
        else:
            doc = [ x for x in explains if x.get('exp') == current_explain ][0]
            en = unicode(pq('.one-en', node).text())
            cn = unicode(pq('.one-ch', node).text())
            doc['sentences'].append({'en':en, 'cn':cn})

    result = {
        'en': unicode(token),
        'level': level,
        'seg': token_seg,
        'phs': phonetics,
        'forms': transforms,
        'exp_sentences': explains
    }
#    pprint(result)
    return result

def update_tokens():
    '''将抓取的页面进行分析，取出token保存'''
    dc_token_coll.ensure_index('en')
    dc_page_coll.ensure_index('en')
    for i, dc_page in enumerate(dc_page_coll.DCPage.find()):
        en = dc_page.en
        dc_token = dc_token_coll.DCToken.find_one({'en': en})

        if not dc_token:
            dc_token = dc_token_coll.DCToken()
            page_info = parse_page(dc_page.content)
            if page_info.get('en'):
                dc_token.update(page_info)
                dc_token.save()
                print i, 'saved', en
            else:
                print i, '!!!!!error', en
        else:
            print i, 'skip', en



#            if page_info.get('en'):
#                dc_token_coll.save(token_doc)
#                print i, 'saved', token
#            else:
#                print i, 'error!!!!!', token
#        else:
#            print i, 'skipped'

def test_page(token):
    coll = db['resource.dictcn.pages']
    coll.ensure_index('token')
    doc = coll.find_one({'token': token})
    print doc.get('html')

def test():
    coll = db['resource.dictcn.pages']
    for i, token in enumerate(tokens.Token.find({'courses': 'IELTS'})):
        page = coll.find_one({'token': token.foreign})

        html = page.get('html')
        result = parse_page(html)
        if not result.get('token'):
            print i, page.get('token')
            page.pop('saved')
            coll.save(page)


if __name__ == '__main__':
#    init_pages_collection()
#    dc_token_coll.drop()
#    update_tokens()
    page = dc_page_coll.Page.find_one({'en': u'apply'})
    print page.content