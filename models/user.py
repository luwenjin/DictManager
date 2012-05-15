#coding: utf-8
from datetime import datetime

from mongokit import Document, ObjectId

from ._base import DB_NAME, users

class User(Document):
    __database__ = DB_NAME
    __collection__ = users.name
    structure = {
        'name': unicode,
        'password': unicode,
        'role': unicode, #'admin', 'editor'
        'token_range': [ObjectId, ObjectId],
        'created_at': datetime,
        'last_login': datetime,
        'ban': bool,
    }
    default_values = {
        'role': u'editor',
        'ban': False,
        }
    indexes = [
            {'fields': ['name']},
    ]
    use_dot_notation = True

    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):
        if not self.get('_id'):
            self.created_at = datetime.now()
        Document.save(self, uuid, validate, safe, *args, **kwargs)