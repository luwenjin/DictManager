# coding: utf-8
""" import all kinds of resources into main db """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
from collections import Counter

from models import db, Sentence, qj_sentence_coll, sentences


def fill_qiji_sentences():
    for i, qj_sen in enumerate(qj_sentence_coll.find()):
        qj_hash = Sentence.make_hash(qj_sen['en'])
        sen = db.Sentence.find_one({'hash': qj_hash})
        if not sen:
            sen = db.Sentence()
            sen.en = qj_sen['en']
            sen.cn = qj_sen['cn']
            print qj_sen['en'], qj_sen['cn']
            print qj_sen['include']
        else:
            print 'skip:', sen.en

        sen.include.update(qj_sen['include'])
        sen.sources.add(u'qiji')
        sen.save()


def fill_dictcn_sentences():
    pass




if __name__ == '__main__':
#    db.sentences.drop()

    fill_qiji_sentences()


