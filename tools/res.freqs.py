# coding: utf-8
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
# ---------------------------------
import csv
import re

from pyquery import PyQuery as pq

from models import freq_coll, cl_token_coll, Token, cl_freq_page_coll


# not good for freq
def fill_SUBTLEX():
    """
    The word. This starts with a capital when the word more often starts with an uppercase letter than
        with a lowercase letter.
    FREQcount. This is the number of times the word appears in the corpus (i.e., on the total of 51 million words).
    CDcount. This is the number of films in which the word appears (i.e., it has a maximum value of 8,388).
    FREQlow. This is the number of times the word appears in the corpus starting with a lowercase letter.
        This allows users to further match their stimuli.
    CDlow. This is the number of films in which the word appears starting with a lowercase letter.
    SUBTLWF. This is the word frequency per million words. It is the measure you would preferably use
        in your manuscripts, because it is a standard measure of word frequency independent of the corpus
        size. It is given with two digits precision, in order not to lose precision of the frequency counts.
    Lg10WF. This value is based on log10(FREQcount+1) and has four digit precision.
        Because FREQcount is based on 51 million words, the following conversions apply for SUBTLEXUS:
    SUBTLCD indicates in how many percent of the films the word appears.
        This value has two-digit precision in order not to lose information.
    Lg10CD. This value is based on log10(CDcount+1) and has four digit precision.
        It is the best value to use if you want to match words on word frequency.
        As CDcount is based on 8388 films, the following conversions apply:
    """
    reader = csv.DictReader(open('data/freq/SUBTLEXusfrequencyabove1.csv'))
    int_fields = ['FREQcount','FREQlow','Cdlow','CDcount']
    float_fields = ['Lg10CD','SUBTLWF','SUBTLCD','Lg10WF',]
    for i, row in enumerate(reader):
        for key in row:
            if key in int_fields:
                row[key] = int(row[key])
            elif key in float_fields:
                row[key] = float(row[key])


        doc = {
            'en': unicode(row['Word']).lower(),
            'SUBTLWF': row['SUBTLWF'] * ( 1.0 * row['FREQlow']/ row['FREQcount'] )
        }
        Doc = {
            'en': unicode(row['Word']).capitalize(),
            'SUBTLWF': row['SUBTLWF'] * ( 1 - 1.0 * row['FREQlow']/ row['FREQcount'] )
        }

        for doc in [doc, Doc]:
            freq_doc = freq_coll.find_one({'en': doc['en']})
            if freq_doc:
                freq_doc.update(doc)
            else:
                freq_doc = doc
            freq_coll.save(freq_doc)
            print i, freq_doc


def is_gram_valid(gram):
    try:
        gram = unicode(gram)
    except:
        return False
    must_not_be = ur'.-\''
    must_not_have = ur'"():*?[];!•1234567890$/<>^+#'
    p = re.compile(ur'\"|\(|\)|\:|\*|\?|\[|\]|;|!|•|1|2|3|4|5|6|7|8|9|0|\$|\/|\<|\>|\^|\+|\#')
    for c in must_not_be:
        if c == gram:
            return False
#    for c in must_not_have:
#        if c in gram:
#            return False
    if p.findall(gram):
        return False
    return True

def filter_ngram1():
    from zipfile import ZipFile
    from collections import Counter
    file_path_template = 'data/freq/google_ngram/googlebooks-eng-fiction-all-1gram-20090715-%s.csv.zip'
    file_name_template = 'googlebooks-eng-fiction-all-1gram-20090715-%s.csv'
    writer = csv.writer(open('data/freq/google_ngram_filtered.csv', 'wb+'), delimiter="\t")
    counter = Counter()
    for i in range(10):
        zf = ZipFile(file_path_template % i)

        f = zf.open(file_name_template % i)


        print file_name_template % i

        for j, row in enumerate(f):
            row = row.strip().split('\t')
            if j % 100000 == 0:
                print i, j, row
            if not len(row)>2:
                continue

            en = row[0].decode('utf-8')
            year = int(row[1])
            count = int(row[2])
            if year< 1950:
                continue
            counter[en] += count

    for i, en in enumerate(counter):
        count = counter[en]
        if not is_gram_valid(en):
            continue
        writer.writerow([en.encode('utf-8'), counter[en]])
        if i % 10000 == 0:
            print i, en


def sync_en_from_tokens():
    for i, token in enumerate(Token.query()):
        en = token.en
        freq_doc = freq_coll.find_one({'en': en})
        if not freq_doc:
            doc = {'en':en}
            freq_coll.save(doc)
            print i, 'saved', en
        else:
            print i, 'skipped', en


def fill_google_ngram():
    """把google ngram里面的数据同步到数据库里面（前提是数据库里面有相应的en，否则太大）"""
    gn_dict = {}
    for line in open('data/freq/google_ngram_filtered.csv'):
        en, count = line.strip().split('\t')
        en = en.decode('utf-8')
        count = int(count)
        gn_dict[en] = count

    for i, freq_doc in enumerate(freq_coll.find()):
        en = freq_doc['en']
        count = gn_dict.get(en)
        if count:
            freq_doc['gn_count'] = count
        else:
            freq_doc['gn_count'] = -1
        freq_coll.save(freq_doc)
        print i, en, count


def parse_collins_hits(page_html):
    d = pq(page_html)
    table = d('table').eq(0)
    hits = pq('b', table).eq(1).text()

    try:
        hits = int(hits)
        return hits
    except:
        return None


def fill_collins_hits():
    for i, freq_doc in enumerate(freq_coll.find()):
        en = freq_doc['en']

        wordbank_page = cl_freq_page_coll.find_one({'en': en})
        if wordbank_page:
            hits = parse_collins_hits(wordbank_page['content'])
            if not hits:
                hits = -1
            freq_doc['cl_hits'] = hits
            cl_token_coll.save(freq_doc)
            print i, en, hits


def fill_collins_current():
    for i, freq_doc in enumerate(freq_coll.find()):
        en = freq_doc['en']
        cl_token = cl_token_coll.find_one({'en': en})

        if cl_token and cl_token.get('current') and cl_token['current'] > 0:
            current = cl_token['current']
        else:
            current = -1

        freq_doc['cl_current'] = current
        freq_coll.save(freq_doc)
        print i, en, current, hits


def export_freq_csv():
    fields = ['en', 'SUBTLWF', 'gn_count', 'cl_current', 'cl_hits']
    f = open('data/freq/exported_freq_coll.csv', 'w+')

    f.write(','.join(fields) + '\n')
    for i, freq_doc in enumerate(freq_coll.find()):
        for field in fields:
            if not freq_doc.has_key(field):
                freq_doc[field] = -1

        template = ','.join(['%('+x+')s' for x in fields]) + '\n'

        line = template % freq_doc
        f.write(line.encode('utf-8'))
        print i, line
    f.close()


if __name__ == '__main__':
    fill_collins_current()


