# coding: utf-8
""" all data models """
import re
from datetime import datetime
from hashlib import md5

from mongokit import ObjectId, Set

from _base import db, DB_NAME, conn, Doc
from _colls import *


@conn.register
class Token(Doc):
    __database__ = DB_NAME
    __collection__ = tokens.name
    structure = {
        'hash': unicode, # lower case 'en', auto modify on save
        'en': unicode, # from qiji
        '_en': Set(unicode), # ill formed en, maybe alias,
        'freq': float, # 0.0 - 1.0, -1 for empty
        'spells': Set(unicode), # eg: mr mr. Mr Mr.
        'phs': Set(unicode), # from iciba(best)
        'exp':{
            'core': unicode,
            'cn': [{'pos': [unicode], 'text': unicode}],
            },
        'courses': Set(unicode), # course names

        'tags': Set(unicode), # trash, word/phrase
        'note': unicode, # 备注字段

        'modify_time': datetime, #auto modify on save
        'create_time': datetime, #auto modify on save
    }
    default_values = {
        'freq': -1.0,
        'exp.cn': [],
        'exp.core': u'',
        'note': u'',
        '_en': set(),
        }
    indexes = [
            {'fields': ['en']},
            {'fields': ['hash']},
            {'fields': ['courses']},
    ]
    use_dot_notation = True
    schemeless = True

    @staticmethod
    def get_token(en):
        doc = db.Token.find_one({'en': unicode(en)})
        return doc

    @classmethod
    def normalize(cls, en):
        # ... 加上左右空格
        en = re.sub('\.\.+', ' ... ', en)

        # sb/sb. -> sb.
        en = re.sub('''(?i)(\W|\A)(sb\.?)(\Z|\W)''', r'\1sb.\3', en)

        # sth/sth. -> sth.
        en = re.sub('''(?i)(\W|\A)(sth\.?)(\Z|\W)''', r'\1sth.\3', en)

        # 去除多余的连续空格
        en = re.sub('\s\s+', ' ', en)
        return en.strip()

    @classmethod
    def make_hash(cls, en):
        return en.strip().lower()

    def trash(self, flag):
        if flag:
            self.tags.add(u'trash')
        else:
            self.tags.discard(u'trash')

    def before_save(self):
        self.en = self.en.strip()
        self.spells.add(self.en)
        self.hash = Token.make_hash(self.en)
        self.freq = float(self.freq)

        type = u'word'
        for x in ['.', ' ', '/']:
            if x in self.en:
                type = u'phrase'
                break

        self.tags.difference_update([u'word', u'phrase'])
        self.tags.add(type)

        self.modify_time = datetime.now()
        if not self.get('_id'):
            self.create_time = datetime.now()


@conn.register
class User(Doc):
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


@conn.register
class Sentence(Doc):
    __database__ = DB_NAME
    __collection__ = sentences.name
    structure = {
        'hash': unicode, #从en生成
        'en': unicode,
        'cn': unicode,
        'include': Set(unicode), # 内含的单词

        'votes': { unicode: int }, # word: vote

        'sources': Set(unicode), # 来源
        'create_time': datetime,
        'modify_time': datetime,
        }
    required_fields = ['en', 'cn', 'hash']
    default_values = {
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
        cur = db.Sentence.find({'include': token.en}, sort=[('_id', 1)])
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


@conn.register
class Diff(Doc):
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


if __name__ == '__main__':
    for i, token in enumerate(db.Token.find()):
        token['_en'] = set()
        token.save()
        print token.en

