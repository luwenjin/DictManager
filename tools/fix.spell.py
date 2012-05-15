#coding:utf-8
import sys
import os
from pprint import pprint
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
from models import db, tokens
from pymongo.objectid import ObjectId
from pyquery import PyQuery as pq


def list_misspell():
    pass