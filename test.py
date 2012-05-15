#coding:utf-8
import sys
import os
parent_path = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(parent_path)
#------------------------------------------------------
from models import tokens, wn_token_coll

count = 0
for i, token in enumerate(tokens.Token.find({"courses": 'IELTS', 'is_trash': False})):
    wn_token = wn_token_coll.WNToken.find_one({'en': token.en})
    if not wn_token or len(wn_token)<=1:
        count += 1
        print count, token.en
        token['mark'] = True
        token.save()
