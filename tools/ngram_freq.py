#coding:utf-8
import os

import pymongo
from nltk.stem.wordnet import WordNetLemmatizer

wnl = WordNetLemmatizer()
ngram_folder = os.path.abspath('../../../resources/ngram')
print os.listdir(ngram_folder)

conn = pymongo.Connection()
db = conn['SuiShouBei']
colls = [
    db['ngram.1'],
    db['ngram.2'],
    db['ngram.3'],
    db['ngram.4'],
    db['ngram.5']
]
tokens = db['tokens']


def get_grams_count(line):
    items = line.strip().split()
    grams = items[:-1]
    count = int(items[-1])
    return map(unicode, grams), count

def is_gram_valid(gram):
    try:
        gram = unicode(gram)
    except:
        return False
    must_not_be = ur'.-\''
    must_not_have = ur'"():*?[];!•1234567890$/<>^+#'
    for c in must_not_be:
        if c == gram:
            return False
    for c in must_not_have:
        if c in gram:
            return False
    return True


def is_all_grams_valid(grams):
    for gram in grams:
        if not is_gram_valid(gram):
            return False
    return True

def purify_ngram_files():
    valid_ngram_file = open('valid_ngram.txt', 'w+')
    invalid_ngram_file = open('invalid_ngram.txt', 'w+')
    
    for file_name in os.listdir(ngram_folder):
        print file_name
        file_path = os.path.join(ngram_folder,file_name)
        for line in open(file_path):
            try:
                grams, count = get_grams_count(line)
            except:
                print line
                continue
            if not is_all_grams_valid(grams):
                invalid_ngram_file.write(line)
            else:
                valid_ngram_file.write(line)

    valid_ngram_file.close()
    invalid_ngram_file.close()


def get_lemmas(grams):
    lemmas = [wnl.lemmatize(x) for x in grams]
    return lemmas

def save_all_grams():
    for coll in colls:
        coll.drop()
    for i, line in enumerate(open('valid_ngram.txt')):
        if i % 10000 == 0:
            print '%0.2f%%' % (100.0*i/1700/10000)
        grams, count = get_grams_count(line)
        lemmas = get_lemmas(grams)

        doc = {
            'ngram': ' '.join(grams),
            'lemmas': lemmas,
            'count': count
        }
        n = len(grams)
        coll = colls[n-1]
        coll.insert(doc, manipulate=False)

def get_freq(grams):
    for coll in colls:
        coll.ensure_index('lemmas')
        coll.ensure_index('ngram')
    n = len(grams)
    if n > 5:
        return None
    coll = colls[n-1]
    lemmas = get_lemmas(grams)
    doc = coll.find_one({'ngram': ' '.join(grams)})
    if doc:
        return doc['count']
    else:
        return None


def test_all_freq():
    lines = open('freq_miss.txt').readlines()
    if len(lines) == 0:
        lines = open('tokens.txt').readlines()
    f1 = open('freq.txt', 'w+')
    f2 = open('freq_miss.txt', 'w+')
    for i, line in enumerate(lines):
        if i % 100 == 0:
            print i
        foreign = unicode(line.strip())
#        print foreign
        grams = foreign.split(' ')
        freq = get_freq(grams)
        
        if freq:
            f1.write( '%s\t%s\n' % (foreign, freq))
        else:
            f2.write( '%s\n' % foreign )
    f1.close()
    f2.close()

def overwrite_all_freq():
    for token in tokens.find():
        foreign = token['foreign']
        grams = foreign.strip().split()
        freq = get_freq(grams)
        token['frequency'] = freq
        tokens.save(token)
        print foreign, freq


def export_all_tokens():
    f = open('tokens.txt', 'w+')
    for i, token in enumerate(tokens.find()):
        if i % 10000 == 0:
            print i
        foreign = token['foreign']
        f.write('%s\n' % foreign)
    f.close()


if __name__ == '__main__':
    overwrite_all_freq()