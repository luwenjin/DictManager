# coding: utf-8
""" import all phonetic resource """
import os, sys
parent_path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(parent_path)
#-------------------------------------------------
from models import yd_simple_token_coll, db


def fill_yd_phs():
    query = { 'phs': [] }
    for i, token in enumerate(db.Token.find(query)):
        en = token.en

        yd_token = yd_simple_token_coll.find_one({'en': en})
        if yd_token and yd_token['phs']:
            token.phs = yd_token['phs']
            token.save()
            print token.en, token.phs
        else:
            print '.....skip', token.en, token.phs

if __name__ == '__main__':
    fill_yd_phs()