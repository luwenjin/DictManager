#coding:utf-8
import sys
import os

parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
import urllib
import re
from lxml import etree
import HTMLParser

import requests
import workerpool

from models import tokens, db, \
    yd_21yh_page_coll, yd_simple_token_coll, yd_detail_page_coll, yd_simple_page_coll


def fetch_simple_xml(en):
    """抓取有道简明解释的xml"""
    try:
        encoded_token = urllib.quote(en)
    except:
        en = ''.join(re.findall("[a-zA-Z\-\s\'\.]+", en))
        encoded_token = urllib.quote(en)
    url = 'http://dict.youdao.com/fsearch?keyfrom=deskdict.instant&q=' + encoded_token + '&pos=-1&doctype=xml&xmlVersion=3.3&dogVersion=1.0&client=deskdict&id=b0695430f503a8333&vendor=qiang.youdao&in=YoudaoDictFull&appVer=4.4.28.9462&appZengqiang=1&le=eng&xslVer=3.0&LTH=203'

    xml = requests.get(url, headers={'user-agent': 'Yodao Desktop Dict (Windows 6.1.7600)'}).content
    return xml


def fetch_detail_xml(en):
    """抓取有道详细解释的xml"""
    try:
        encoded_en = urllib.quote(en)
    except:
        en = ''.join(re.findall("[a-zA-Z\-\s\'\.]+", en))
        encoded_en = urllib.quote(en)
    url = 'http://dict.youdao.com/search?keyfrom=deskdict.main&q=' + \
          encoded_en + \
          '&xmlDetail=true&doctype=xml&xmlVersion=7.1&dogVersion=1.0&client=deskdict&id=0695430f503a8313&vendor=qiang.youdao&in=YoudaoDictFull_(1)&appVer=5.0.32.4695&appZengqiang=1&le=eng&xslVer=3.0&LTH=156'
    xml = requests.get(url, headers={'user-agent': 'Yodao Desktop Dict (Windows 6.1.7600)'}).content
    return xml


def import_21yh_xmls(drop=False):
    file_name, tag_end = '21yh.xml', '</word>'
    file_path = 'data/' + file_name
    document = open(file_path).read()

    blocks = document.split(tag_end)
    count = len(blocks)

    if drop:
        yd_21yh_page_coll.drop()
        yd_21yh_page_coll.ensure_index('en')

    for i, block in enumerate(blocks):
        xml = block + tag_end
        tree = etree.fromstring(xml)
        li = [x.text for x in tree.findall('return-phrase/l/i')]
        if li:
            en = unicode(li[0])
            page = yd_21yh_page_coll.find_one({'en': en})
            if page:
                print i, '/', count, '----skip', en
            else:
                print i, '/', count, 'save', en
                page = yd_21yh_page_coll.Page()
                page.en = en
                page.content = xml.decode('utf-8')
                page.save()


def sync_all_page_xml(type="detail", overwrite=False):
    """获取所有没有入库的xml(detail/simple)"""
    if type == 'detail':
        coll = yd_detail_page_coll
        fetch = fetch_detail_xml
    else:
        coll = yd_simple_page_coll
        fetch = fetch_simple_xml

    coll.ensure_index('en')
    i = 0

    def fetch_and_save(en):
        page = coll.find_one({'en': en})

        if overwrite or\
           not page or\
           not page['content'] or\
           '503 Service Temporarily Unavailable' in page['content']:
            content = fetch(en)

            if i % 100 == 0:
                print content

            if '<block>' in content:
                print 'blocked'
                return
            if '503 Service Temporarily Unavailable' in content:
                print '503'
                return

            if page:
                coll.remove(page['_id'])

            page = {
                'en': en,
                'content': content
            }

            coll.save(page)
            print en, 'saved'
        else:
            print en, 'skipped'


    pool = workerpool.WorkerPool(size=10)
    pool.map(fetch_and_save, [x['en'] for x in tokens.find()])

    pool.shutdown()
    pool.wait()


def parse_detail_xml(content):
    h = HTMLParser.HTMLParser()
    et = etree.XML(content.encode('utf-8'))

    s_rules = {
        'en': '//input/text()',
        'phs': '//word/phone/text()',
    }

    li_rules = {
        'spells': '//word/*/l/i/text()',
        'speech': '//word/speech/text()'
    }

    doc = {}
    for name in s_rules:
        rule = s_rules[name]
        li = et.xpath(rule)
        doc[name] = h.unescape(li[0]) if li else u''

    for name in li_rules:
        rule = li_rules[name]
        li = et.xpath(rule)
        doc[name] = [h.unescape(x) for x in li]

    # after process
    spells = doc['spells'] + [doc['en']]
    spells = set(spells)
    doc['spells'] = []
    for spell in spells:
        if not re.match('\d+', spell):
            doc['spells'].append(spell)

    phs = doc['phs']
    if phs:
        phs = [x.strip() for x in phs.split(';')]
        doc['phs'] = phs
    else:
        doc['phs'] = []


    return doc



def import_tokens():
    xml_coll = db['resource.youdao.meaning_xml']
    token_coll = db['resource.youdao.tokens']
    token_coll.ensure_index('token')
    for i, xml_doc in enumerate(xml_coll.find()):
        token_text = xml_doc.get('token')
        meaning_list = parse_meaning_xml(xml_doc.get('xml'))
        if len(meaning_list) > 0:
            token = token_coll.find_one({'token': token_text})
            if not token:
                token = {
                    'token': token_text,
                    'meaning': '|'.join(meaning_list)
                }
                token_coll.save(token)
                print i, 'update:', token_text


def parse_meaning_xml(xml):
    tree = etree.fromstring(xml.encode('utf-8'))
    lines = [x.text for x in tree.findall('custom-translation/translation/content')]
    return lines


def get_detail_page_tree(content):
    error_bytes = [u'\x00', u'\x01', u'\x12', u'\x07']
    try:
        tree = etree.fromstring(content.encode('utf-8'))
        return tree
    except:
        for error_byte in error_bytes:
            content = content.replace(error_byte, '')
        try:
            tree = etree.fromstring(content.encode('utf-8'))
            return tree
        except:
            return None


def import_simple_tokens():
    count = yd_detail_page_coll.count()
    yd_simple_token_coll.ensure_index('en')
    for i, page in enumerate(yd_detail_page_coll.Page.find()):
        percentage = '%0.2f%%' % (100.0 * i / count)
        en = page.en
        simple_token = yd_simple_token_coll.YDSimpleToken.find_one({'en': en})
        if simple_token:
        #            print i, percentage, '---skip', en
            continue
        else:
            tree = get_detail_page_tree(page.content)
            if tree is None: continue

            block = tree.find('basic/[type="ec"]/simple-dict')
            if block is None: continue

            simple_token = yd_simple_token_coll.YDSimpleToken()
            simple_token.en = en
            simple_token.return_en = unicode(block.findtext('.//return-phrase//i'))
            simple_token.phs = [unicode(x.strip()) for x in re.split('[;,]', block.findtext('.//phone', ''))]
            simple_token.speech = unicode(block.findtext('.//speech'))
            simple_token.exps_cn = [unicode(x.text.strip()) for x in block.findall('.//trs//i')]
            for wf in block.findall('.//wf'):
                type = unicode(wf.findtext('name'))
                text = unicode(wf.findtext('value'))
                simple_token.forms.append({'type': type, 'text': text})

            rel_words_block = tree.find('basic/[type="rel-word"]/rel-word-dict')
            if rel_words_block is not None:
                simple_token.stem = unicode(rel_words_block.findtext('stem'))
                rel_li = rel_words_block.findall('.//rel')
                for rel in rel_li:
                    rel_doc = {
                        'POS': unicode(rel.findtext('.//pos')),
                        'words': []
                    }
                    en_nodes = rel.findall('.//word')
                    cn_nodes = rel.findall('.//tran')
                    en_cn_pairs = zip(en_nodes, cn_nodes)
                    for en_node, cn_node in en_cn_pairs:
                        en = en_node.text
                        cn = cn_node.text
                        rel_doc['words'].append({
                            'en': unicode(en),
                            'cn': unicode(cn)
                        })
                    simple_token.rels.append(rel_doc)
                #            pprint(simple_token)
            simple_token.save()
            print i, percentage, 'saved', en


def load_stem(overwrite=False):
    for i, token in enumerate(tokens.Token.find({'is_trash': False, 'courses': 'IELTS'})):
        simple_token = yd_simple_token_coll.YDSimpleToken.find_one({'en': token.en})

        if simple_token and simple_token.stem:
            if overwrite or overwrite == False and not token.stem:
                token.stem = simple_token.stem
                token.save()
                print i, 'saved!', token.en, token.stem
                continue
        print i, 'skip', token.en


def find_block_tokens():
    xml_coll = db['resource.youdao.detail_xml']
    print xml_coll.count()
    for i, doc in enumerate(xml_coll.find()):
        if '<block>' in doc.get('xml') or not doc.get('xml'):
            # <h1>Service Temporarily Unavailable</h1>
            print i, doc.get('token')
            xml_coll.remove(doc)


def test_show_xml():
    file_name, tag_end = 'xhy.xml', '</word>'
    file_path = '../../resources/dicts/' + file_name
    f = open(file_path)
    text = ''
    while 1:
        text = f.read(100 * 1024)
        #        if text.count(tag_end) >= 10:
        #            end_pos = text.rindex(tag_end) + len(tag_end)
        #            text = text[:end_pos]
        break
    xml_file = open('data/test.xml', 'w+')
    xml_file.write('<root>' + text + '</root>')
    xml_file.close()


if __name__ == '__main__':

#    sync_all_page_xml('detail', overwrite=False)
    for page in yd_detail_page_coll.find():
        xml = page['content']
        doc = parse_detail_xml(xml)

        if doc['phs'] and len(doc['phs'])> 1:

            print doc['en'], doc['phs']
