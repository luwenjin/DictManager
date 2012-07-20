import os

MONGO_BIN_PATH = 'D:/Program Files/mongodb/bin'

coll_names = [
    'users',
    'tokens',
    'sentences',
    'diffs',
    'core_exp',
    'resource.qiji.tokens',
    'resource.dictcn.tokens',
    'resource.youdao.simple_tokens',
    'resource.wordnet.tokens',
    'resource.google_translate.tokens',
]

os.chdir(MONGO_BIN_PATH)
for name in coll_names:
    cmd = 'mongodump -d dict -c %s' % name
    os.system(cmd)

