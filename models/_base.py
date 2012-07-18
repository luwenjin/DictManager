#coding:utf-8
from mongokit import Connection, Document

DB_NAME = 'dict'

conn = Connection('127.0.0.1')
db = conn[DB_NAME]
