import os
import sys

sys.path.append( os.path.abspath('../..'))
from models import db, tokens


def update_rank():
    freq_20k_count = tokens.find({'freq_20k': {'$ne':None}}).count()
    freq_ngram_count = tokens.find({'freq_ngram': {'$ne':None}}).count()

    f = open('rank.txt', 'w+')

    for token in tokens.find({'rank': None}):
        if token.get('rank'):
            continue

        freq_20k = token.get('freq_20k')
        freq_ngram = token.get('freq_ngram')

        freq_20k_pos = 0
        freq_ngram_pos = 0

        if freq_20k:
            freq_20k_pos = tokens.find({'freq_20k': {'$lte': freq_20k}}).count()
        if freq_ngram:
            freq_ngram_pos = tokens.find({'freq_ngram': {'$lte': freq_ngram}}).count()

        rank_20k = 1.0*freq_20k_pos/freq_20k_count
        rank_ngram = 1.0*freq_ngram_pos/freq_ngram_count

        if rank_20k and rank_ngram:
            rank = (rank_20k + rank_ngram) / 2
        elif rank_20k:
            rank = rank_20k
        elif rank_ngram:
            rank = rank_ngram
        elif token.get('rank'):
            rank = token.get('rank')
        else:
            rank = None
        token['rank'] = rank
        tokens.save(token)

        line = '%s\t%0.2f\t%0.2f\n' % (
            token.get('foreign'),
            1.0*freq_20k_pos/freq_20k_count,
            1.0*freq_ngram_pos/freq_ngram_count
        )
        f.write(line)
        print line,
    f.close()



if __name__ == '__main__':
    update_rank()