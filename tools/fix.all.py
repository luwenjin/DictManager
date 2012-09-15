# coding: utf-8
""" import all kinds of resources into main db """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
# -----------------------------------
from models import db, Token


def fix_spells_and_sentence_include():
    """修正拼写不规范的地方，并且修正例句的include"""
    for i, token in enumerate(db.Token.find()):
        en = token.en
        norm_en = Token.normalize(token.en)
        sent = db.Sentence.find_one({'include': en})
        if en != norm_en:
            print en, '->', norm_en
            token._en.add(en)
            token.en = norm_en
            token.save()
            if sent:
                sent.include.discard(en)
                sent.include.add(norm_en)
                sent.save()
                print sent.en
            print '-------------'


if __name__ == '__main__':
    fix_spells_and_sentence_include()

