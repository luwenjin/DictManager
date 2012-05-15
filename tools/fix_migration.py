# coding: utf-8
"""本文件的作用是临时运行一下，用来修复代码修改过程中的数据库不兼容问题"""

import pymongo

conn = pymongo.Connection()
db = conn.dict
coll = db.tokens

for i, token in enumerate(coll.find()):
    is_trash = token.get('trash')
    if is_trash is None:
        continue
    token['is_trash'] = is_trash
    coll.save(token)
    print i, token['en'], is_trash