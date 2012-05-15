from mongokit import Document

from ._base import DB_NAME


class Difference(Document):
    __database__ = DB_NAME
    __collection__ = 'differences'
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
