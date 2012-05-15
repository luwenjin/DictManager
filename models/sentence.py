#coding:utf-8
from datetime import datetime
from hashlib import md5
import re

from mongokit import Document, ObjectId

from ._base import DB_NAME, sentences

class Sentence(Document):
    __database__ = DB_NAME
    __collection__ = sentences.name
    structure = {
        'en': unicode,
        'cn': unicode,
        'hash': unicode, #从en生成
        'include': [unicode], # 内含的单词
        'created_at': datetime,
        'modified_at': datetime,
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
    def get_hash(en):
        if not en:
            return None
        low_en_list = [ word.lower().strip() for word in re.findall('[a-zA-Z]+', en) ]
        en_md5 = md5(' '.join( low_en_list )).hexdigest()
        return unicode(en_md5)

    @staticmethod
    def get_token_sentences(token):
        cur = sentences.Sentence.find({'include': token.en}, sort=[('_id', 1)])
        return list(cur)

#    def ban_course(self, en, course):
#        course = unicode(course)
#        self.tokens
#        token_text_list = [x.get('text') for x in token.get('foreign')]
#        for _token in self.tokens:
#            if _token.get('text') in token_text_list:
#                if course not in _token.get('banned_courses', []):
#                    _token.setdefault('banned_courses', [])
#                    _token['banned_courses'].append(course)
#                    return True
#        return False
#
#    def permit_course(self, token, course):
#        course = unicode(course)
#        token_text_list = [x.get('text') for x in token.get('foreign')]
#        for _token in self.tokens:
#            if _token.get('text') in token_text_list:
#                if course in _token.get('banned_courses', []):
#                    _token.setdefault('banned_courses', [])
#                    if course in _token['banned_courses']:
#                        _token['banned_courses'].remove(course)
#                        return True
#        return False
#
#    def get_banned_courses(self, token_text):
#        token_text = unicode(token_text)
#        for token in self.tokens:
#            if token_text == token.get('text'):
#                return token.get('banned_courses', [])
#        return None
#
#    def is_banned(self, token_text, course):
#        token_text = unicode(token_text)
#        course = unicode(course)
#        banned_courses = self.get_banned_courses(token_text)
#        if course in banned_courses:
#            return True
#        else:
#            return False


    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):
        self.modified_at = datetime.now()
        if not self.get('_id'):
            self.created_at = datetime.now()
        self.hash = Sentence.get_hash(self.en)
        Document.save(self, uuid, validate, safe, *args, **kwargs)

if __name__ == '__main__':
    pass