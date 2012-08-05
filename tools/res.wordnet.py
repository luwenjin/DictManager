#coding:utf-8
import sys
import os
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
import operator

from models import tokens, Token, wn_token_coll

from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer

def load_lemmas():
    lemma_list = [ x for x in wn.all_lemma_names() ]
    for i, lemma in enumerate(lemma_list):
        lemma = unicode(lemma.replace('_', ' '))
#        if re.findall('[^a-zA-Z0-9\s\-\'\./]', lemma):
#            print lemma

        tokens.ensure_index('en')
        token = Token.get_token(lemma)
        if not token:
            token = tokens.Token()
            token.en = lemma
            token.save()
#            print i, 'saved', lemma
        else:
            print i, 'skipped', lemma

def update_tokens_lemma():
    wnl = WordNetLemmatizer()
    for i, token in enumerate(tokens.Token.find({"courses": 'IELTS', 'is_trash': False})):
        lemma = wnl.lemmatize(token.en)
        if lemma != token.en:
            print token.en, lemma

def split_synset_name(name):
    li = name.split('.')
    token = '.'.join(li[:-2]).replace('_', '')
    POS = li[-2]
    idx = li[-1]
    return token, POS, idx


def import_tokens():
    wn_token_coll.drop()
    wn_token_coll.ensure_index('en')
    for i, token in enumerate(tokens.Token.find({"courses": 'IELTS', 'is_trash': False})):
        wn_token = wn_token_coll.WNToken()
        wn_token.en = token.en

        lemma_name = token.en.replace(' ', '_')
        exps = []
        for lemma in wn.lemmas(lemma_name):
            synset_token, POS, idx = split_synset_name(lemma.synset.name)
            text = lemma.synset.definition
            count = lemma.count()
            doc = {
                'POS': unicode(POS),
                'text': unicode(text),
                'synset_token': unicode(synset_token),
                'count': count
            }
            exps.append(doc)
        if exps:
            exps.sort(key = operator.itemgetter('count'), reverse=True)
            wn_token.exps = exps
            wn_token.save()
        print i, token.en, [ x.get('count') for x in exps ]

#        print token, pos, idx



if __name__ == '__main__':
    import_tokens()