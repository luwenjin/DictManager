#coding:utf-8
import time
import sys
import os
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------

from models import tokens, frequencies, ngrams

w = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-\.'



def is_pure_word(word):
    result = True
    for c in word:
        if c not in w:
            result = False
            break
    return result

def import_frequency():
    data = {}
    for line in open('../resources/freq500k.txt'):
        items = line.strip().split()
        lemma = unicode(items[1])
#        pos = unicode(items[2])
        count = long(items[3])
#        dispersion = float(items[4])
        data.setdefault(lemma, 0)
        data[lemma] += count

    for lemma in data:
        count = data[lemma]
#        frequency = frequencies.Frequency.find_one({'lemma': lemma})
#        if frequency:
#            continue
        frequency = frequencies.Frequency()
        frequency.lemma = lemma
        frequency.count = count
        print lemma, count
        frequency.save()

def sync_frequency():
    for token in tokens.Token.find():
        freq = frequencies.Frequency.find_one({'lemma': token.foreign})
        if freq:
            token.frequency = freq.count
            print freq.lemma, freq.count
        else:
            token.frequency = None
            print token.foreign, '......'
        token.save()

def shrink_ngram_to_data( enumerate_obj ):
    data = {}
    bytes = 0
    for i,line in enumerate_obj:
        bytes += len(line)
        if i%1000000 == 100:
            print '%s\t%0.2fMB'% (i, bytes/1024.0/1024)
        items = line.split('\t')
        ngram = items[0]
        try:
            year = int(items[1])
        except:
            continue
        count = int(items[2])
        if year > 1990:
            data.setdefault(ngram,0)
            data[ngram] += count
    return data

def shrink_all_ngram():
    from zipfile import ZipFile
    src_folder = 'D:/TDDOWNLOAD/ngram'
    target_folder = '../resources/ngram'

    src_zip_file_names = [x for x in os.listdir(src_folder) if x.endswith('.zip')]
    for i, zip_file_name in enumerate(src_zip_file_names):
#        if i%2 == 1: continue
        zip_file_path = os.path.join(src_folder, zip_file_name)
        zip_file = ZipFile(zip_file_path)
        csv_file_name = zip_file_name.replace('.zip', '')
        target_file_path = os.path.join(target_folder, csv_file_name)
        if os.path.exists(target_file_path):
            print csv_file_name, 'exists!  skip'
            continue
        else:
            print 'Shrinking: %s ...' % csv_file_name
        enumerate_obj = enumerate(zip_file.open(csv_file_name))
        data = shrink_ngram_to_data( enumerate_obj )
        print 'writing %s ...' % csv_file_name
        with open(target_file_path, 'w+') as f:
            for ngram in data:
                count = data[ngram]
                if count < 1000:
                    continue
                line = '%s\t%s\n' % (ngram, count)
                f.write(line)

def import_ngrams():
    folder = '../resources/ngram'
    ngrams.drop()
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)

        print file_name
        data = {}
        for i, line in enumerate(open(file_path)):
            if i % 10000 == 0:
                print i
            grams, count = line.strip().split('\t')
            try:
                grams = unicode(grams).lower()
            except:
                continue
            count = long(count)
            gram_list = tuple(grams.split())
            if not is_valid_grams(gram_list):
                continue
            data.setdefault( gram_list, 0)
            data[gram_list] += count
        li = []
        for gram_list in data:
            count = data[gram_list]
            doc = {
                'grams': list(gram_list),
                'count': count
            }
            li.append(doc)
        print 'insert %s ...'% len(li)
        ngrams.insert(li)
    ngrams.ensure_index('grams')

all_valid_words = [x.lower() for x in tokens.distinct('words')]
valid_word_map = dict.fromkeys(all_valid_words)

def is_valid_grams(gram_list):
    for gram in gram_list:
        if not valid_word_map.has_key(gram):
            return False
    return True

def udpate_frequency_by_ngrams():
    print tokens.Token.find({'frequency': None}).count()
    for i, token in enumerate(tokens.Token.find()):
        if i%100 == 0:
            print i
        grams = token.foreign.lower().split()
        ngram = ngrams.NGram.find_one({'grams': grams})
        if ngram:
            token.frequency = ngram.count
            token.save()

def show_freq_order():
    for token in tokens.Token.find( sort=[('frequency', -1)]):
        print token.foreign, token.frequency









if __name__ == '__main__':
#    frequencies.drop()
#    import_frequency()
#    frequencies.ensure_index('lemma')
#    import_ngrams()
#    udpate_frequency_by_ngrams()
#    show_freq_order()
#    for ngram in ngrams.NGram.find():
#        print ngram.grams
#    import time
    while 1:
        shrink_all_ngram()
        time.sleep(10)
#    purify_ngrams()