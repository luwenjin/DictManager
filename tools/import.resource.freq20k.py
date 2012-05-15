import os
import sys

sys.path.append( os.path.abspath('../..'))
from models import db, tokens
coll = db['resource.freq20k']


def import_into_db():
    file_path = '../../resources/frequency.txt'
    for line in open(file_path):
        items = [ x.strip() for x in line.split() ]
        rank, word, pos, count, confidence = items
        word = unicode(word)
        count = long(count)
        #word, count
        w = coll.find_one({'word': word})
        if not w:
            w = {
                'word': word,
                'count': count
            }
            coll.save(w)
            print word,count
    coll.ensure_index('word')
    coll.ensure_index('count')

def update_tokens():
    for token in tokens.find():
        if token.get('freq_20k'):
            continue
        foreign = token.get('foreign')
        freq_result = coll.find_one({'word': foreign})
        if freq_result:
            token['freq_20k'] = freq_result.get('count')
            tokens.save(token)
            print 'updated: ', token.get('foreign')

if __name__ == '__main__':
    update_tokens()