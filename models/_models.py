# coding: utf-8
""" all data models """
from datetime import datetime
import re
from hashlib import md5

from mongokit import Document, ObjectId

from _base import db, DB_NAME, conn
from _colls import *


class EasyDocument(Document):
    @classmethod
    def coll(cls):
        return db[cls.__collection__]

    @classmethod
    def coll_model(cls):
        coll = cls.coll()
        model = getattr(coll, cls.__name__)
        return model

    @classmethod
    def new(cls, d=None, **kwargs):
        """ create new Document Object and return
        usage:
            - doc = Model.new({'x':'x','y':'y'})
            - Model.new(x = x, y = y)
        """
        doc = cls.coll_model()()
        if d and type(d) == dict:
            doc.update(d)
        if kwargs:
            doc.update(kwargs)
        return doc

    @classmethod
    def insert(cls, d=None, **kwargs):
        """ insert doc into collection
        usage:
            - doc = Model.insert({'x':'x','y':'y'})
            - Model.insert(x = x, y = y)
        """
        doc = cls.new(d, **kwargs)
        doc.save()
        return doc

    @classmethod
    def one(cls, d=None, **kwargs):
        """ fetch one doc
        usage:
            - Model.one({'x':'x','y':'y'}, sort=[('x',1), ...]), same as pymongo's find_one
            - Model.one(x = x, y = y), this is a shortcut
        """
        model = cls.coll_model()
        if type(d) in [dict, ObjectId]:
            return model.find_one(d, **kwargs)
        elif kwargs:
            return model.find_one(kwargs)
        else:
            return model.find_one()

    @classmethod
    def query(cls, d=None, **kwargs):
        """ query docs, return cursor
        usage:
            - Model.query({'x':'x','y':'y'}, sort=[('x',1), ...]), same as pymongo's find
            - Model.query(x = x, y = y), this is a shortcut
        """
        model = cls.coll_model()
        if type(d) in [dict, ObjectId]:
            return model.find(d, **kwargs)
        elif kwargs:
            return model.find(kwargs)
        else:
            return model.find()

    @classmethod
    def all(cls, d=None, **kwargs):
        """ get docs, return list
        usage:
            - Model.all({'x':'x','y':'y'}, sort=[('x',1), ...]), same as pymongo's find
            - Model.all(x = x, y = y), this is a shortcut
        """
        cur = cls.query(d, **kwargs)
        return list(cur)

    def before_update(self):
        pass

    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):
        Document.save(self, uuid, validate, safe, *args, **kwargs)


class Token(EasyDocument):
    __database__ = DB_NAME
    __collection__ = tokens.name
    structure = {
        'hash': unicode, # lower case 'en', auto modify on save
        'en': unicode,
        'ph': {'en': unicode, 'us': unicode},
        'type': unicode, #word/phrase
        'exp':{
            'core': unicode,
            'cn': [{'pos': [unicode], 'text': unicode}],
            },
        'courses': [unicode], # course names

        'tags': [unicode],
        'note': unicode, # 备注字段
        'is_trash': bool, # 对于某些垃圾词，为防止重复导入，不物理删除，但打上标记

        'modify_time': datetime, #auto modify on save
        'create_time': datetime, #auto modify on save
    }
    default_values = {
        'ph.en': u'',
        'ph.us': u'',
        'exp.cn': [],
        'exp.core': u'',
        'is_trash': False,
        'courses': [],
        'note': u'',
        }
    indexes = [
            {'fields': ['en']},
            {'fields': ['hash']},
            {'fields': ['type']},
            {'fields': ['courses']},
            {'fields': ['is_trash']},
    ]
    use_dot_notation = True

    @staticmethod
    def get_token(en):
        doc = tokens.Token.find_one({'en': unicode(en)})
        return doc

    @classmethod
    def make_hash(cls, en):
        return en.strip().lower()

    def before_update(self):
        self.hash = Token.make_hash(self.en)
        self.type = u'word'
        for x in ['.', ' ', '/']:
            if x in self.en:
                self.type = u'phrase'
                break
        self.modify_time = datetime.now()
        if not self.get('_id'):
            self.create_time = datetime.now()


class User(EasyDocument):
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

    def before_update(self):
        if not self.get('_id'):
            self.created_at = datetime.now()


class Sentence(EasyDocument):
    __database__ = DB_NAME
    __collection__ = sentences.name
    structure = {
        'hash': unicode, #从en生成
        'en': unicode,
        'cn': unicode,
        'include': [unicode], # 内含的单词

        'create_time': datetime,
        'modify_time': datetime,
        }
    required_fields = ['en', 'cn', 'hash']
    default_values = {
        'include': []
    }
    indexes = [
            {'fields': ['include']},
            {'fields': ['hash']},
    ]
    use_dot_notation = True

    @staticmethod
    def make_hash(en):
        if not en:
            return None
        low_en_list = [ word.lower().strip() for word in re.findall('[a-zA-Z]+', en) ]
        en_md5 = md5(' '.join( low_en_list )).hexdigest()
        return unicode(en_md5)

    @staticmethod
    def get_token_sentences(token):
        cur = sentences.Sentence.find({'include': token.en}, sort=[('_id', 1)])
        return list(cur)

    def update_include(self, include):
        if not self.include:
            self.include = []
        self.include = list(set(self.include + include))
        return self.include

    def before_update(self):
        self.hash = Sentence.make_hash(self.en)
        self.modify_time = datetime.now()
        if not self.get('_id'):
            self.create_time = datetime.now()


class Diff(EasyDocument):
    __database__ = DB_NAME
    __collection__ = diffs.name
    structure = {
        'same_meaning': unicode,
        'diff_meanings': [{'word':unicode, 'meaning':unicode}],
        }
    indexes = [
            {'fields':['diff_meanings.word'], 'check': False}
    ]
    use_dot_notation = True

    @property
    def word_list(self):
        return [x['word'] for x in self.diff_meanings]


class CoreExp(EasyDocument):
    __database__ = DB_NAME
    __collection__ = core_exp.name
    structure = {
        'en': unicode,
        'cn': unicode,
        'editions': dict, # cn: [user_names]
        'objections': dict, #reason: [user_names]

        'editors': [unicode],
        'editors_count': int,

        'supporters': [unicode],
        'supporters_count': int,

        'objectors': [unicode],
        'objectors_count': int,

        'actions_count': int,
        'tags': [unicode],
    }
    required_fields = ['en', 'cn']
    default_values = {
        'supporters': [],
        'objectors': [],
        'editors': [],
        'editions': {},
        'objections': {},
    }
    indexes = [
        {'fields': ['editors']},
        {'fields': ['supporters']},
        {'fields': ['objectors']},

        {'fields': ['supporters_count']},
        {'fields': ['objectors_count']},
        {'fields': ['editors_count']},
        {'fields': ['actions_count']},

        {'fields': ['tags']},
    ]
    use_dot_notation = True

    def before_update(self):
        self.supporters_count = len(self.backers)
        self.objectors_count = len(self.objectors)
        self.editors_count = len(self.editors)
        self.actions_count = self.supporters_count + self.objectors_count + self.editors_count

    def remove_user(self, name):
        if name in self.supporters:
            self.supporters.remove(name)
        if name in self.editors:
            self.editors.remove(name)
            for cn in self.editions:
                names = self.editions[cn]
                if name in names:
                    names.remove(name)

        if name in self.objectors:
            self.objectors.remove(name)
            for reason in self.objections:
                names = self.objections[reason]
                if name in names:
                    names.remove(name)

    def add_supporter(self, name):
        self.remove_user(name)
        self.supporters.append(name)

    def add_objector(self, name, reason):
        self.remove_user(name)
        self.objectors.append(name)
        self.objections.setdefault(reason, [])
        self.objections[reason].append(name)

    def add_editor(self, name, cn):
        self.remove_user(name)
        self.editors.append(name)
        self.editions.setdefault(cn, [])
        self.editions[cn].append(name)


conn.register([
    User, Token, Sentence, Diff, CoreExp
])

def fill_load_exp(course_name):
    for i, token in enumerate(Token.query(courses=course_name)):
        if i % 92 != 0:
            continue
        gt_token = gt_token_coll.find_one({'en': token.en})
        core_exp = CoreExp.one(en=token.en)
        if gt_token and not core_exp:
            core_exp = CoreExp.insert(
                en = token.en,
                cn = gt_token['cn']
            )
            print core_exp.en



if __name__ == '__main__':
    core_exp.drop()
    fill_load_exp('IELTS')