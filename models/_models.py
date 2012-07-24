# coding: utf-8
""" all data models """
import re
import random
from datetime import datetime
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

    def before_save(self):
        pass

    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):
        self.before_save()
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

    def before_save(self):
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

    def before_save(self):
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

    def before_save(self):
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
        'options': [{
            'cn': unicode,
            'editor': unicode,
            'voters': [unicode],
            'tag': unicode,
        }],
        'actions_count': int,
        'tags': [unicode],
    }
    required_fields = ['en', 'options']
    default_values = {
        'options': [],
        'tags': [],
    }
    indexes = [
        {'fields': ['en']},
        {'fields': ['options.editor'], 'check': False},
        {'fields': ['options.voters'], 'check': False},
        {'fields': ['options.tag'], 'check': False},
        {'fields': ['actions_count']},
        {'fields': ['tags']},
    ]
    use_dot_notation = True

    @property
    def ordered_options(self):
        return sorted(self.options, key=lambda x:len(x['voters']), reverse=True)

    @property
    def best_option(self):
        best_option_voters = max([len(option['voters']) for option in self.options])
        best_options = [option for option in self.options if len(option['voters']) == best_option_voters]
        return random.choice(best_options)

    def before_save(self):
        self.actions_count = 0
        for option in self.options:
            self.actions_count += len(option['voters'])

    def remove_user(self, name):
        remove_index = -1
        for i, option in enumerate(self.options):
            if option['editor'] == name:
                option['editor'] = None
                del option['voters'][0]
                if option['voters']:
                    option['editor'] = option['voters'][0]
                else:
                    remove_index = i
            elif name in option['voters']:
                option['voters'].remove(name)
        if remove_index >= 0:
            del self.options[remove_index]

    def add_option(self, cn, user_name):
        self.remove_user(user_name)
        option_found = False
        for i, option in enumerate(self.options):
            if option['cn'] == cn:
                option['voters'].append(user_name)
                option_found = True
                break
        if not option_found:
            option = {
                'cn': cn,
                'editor': user_name,
                'voters': [user_name],
                'tag': None,
            }
            self.options.append(option)

    def tag_option(self, cn, tag):
        for i, option in enumerate(self.options):
            if option['cn'] == cn:
                option['tag'] = tag
                self.save()
                return True
        return False



conn.register([
    User, Token, Sentence, Diff, CoreExp
])


def fill_load_exp(course_name):
    for i, token in enumerate(Token.query(courses=course_name)):
        if i % 46 != 0:
            continue
        gt_token = gt_token_coll.find_one({'en': token.en})
        core_exp = CoreExp.one(en=token.en)
        if gt_token and not core_exp:
            core_exp = CoreExp.insert(
                en = token.en,
                options = [{
                    'cn': gt_token['cn'],
                    'editor': u'SYS',
                    'voters': [u'SYS'],
                }]
            )
            print core_exp.en

def migrate_core_exp():
    for ce in core_exp.find():
        if ce.has_key('skippers'):
            ce.pop('skippers')
        for option in ce['options']:
            if not option.has_key('tag'):
                option['tag'] = None
        core_exp.save(ce)
    for ce in CoreExp.all():
        ce.save()




if __name__ == '__main__':
#    core_exp.drop()
#    fill_load_exp('IELTS')
#    print CoreExp.one({'options.editor': u'SYS'})
    migrate_core_exp()