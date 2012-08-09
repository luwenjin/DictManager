#coding:utf-8
from mongokit import Connection, Document

DB_NAME = 'dict'

conn = Connection('127.0.0.1')
db = conn[DB_NAME]


class Doc(Document):
    def before_save(self):
        pass

    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):
        self.before_save()
        Document.save(self, uuid, validate, safe, *args, **kwargs)