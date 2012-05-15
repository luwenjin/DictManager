#coding: utf-8
from datetime import datetime

from mongokit import Document

from ._base import DB_NAME, tokens

class Token(Document):
    __database__ = DB_NAME
    __collection__ = 'tokens'
    structure = {
        'en': unicode,
        'low': unicode, # 小写的en
        'ph_en': unicode,
        'ph_us': unicode,
        'exp_core': unicode,
        'exps_cn': [{'POSs': [unicode], 'text': unicode}],
        'is_phrase': bool,
        'courses': [unicode], # 哪些课程有这个单词？
        'modified_at': datetime,
        'created_at': datetime,
        'trash': bool, # 对于某些垃圾词，为防止重复导入，不物理删除，但打上标记
        'last_editor': unicode,
        'note': unicode, #备注字段
        'src': unicode,
        'mark': bool,
    }
    default_values = {
        'ph_en': u'',
        'ph_us': u'',
        'exps_cn': [],
        'exp_core': u'',
        'trash': False,
        'note': '',
        'last_editor': None,
        'mark': False,
    }
    indexes = [
        {'fields': ['en']},
        {'fields': ['low']},
        {'fields': ['is_phrase']},
        {'fields': ['courses']},
        {'fields': ['trash']},
        {'fields': ['mark']},
    ]
    use_dot_notation = True

    @staticmethod
    def get_token(en):
        doc = tokens.Token.find_one({'en': unicode(en)})
        return doc

    def rename(self, new_en):
        old_en = self.en
        self.en = new_en
        self.save()
        old_token = Token.get_token(old_en)
        if not old_token:
            old_token = tokens.Token()
            old_token.en = old_en
            old_token.trash = True
            old_token.save()
        return True




    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):
        self.low = self.en.lower()
        self.is_phrase = False
        for x in ['.', ' ', '/']:
            if x in self.en:
                self.is_phrase = True

        self.modified_at = datetime.now()
        if not self.get('_id'):
            self.created_at = datetime.now()
        Document.save(self, uuid, validate, safe, *args, **kwargs)