#coding:utf-8
from mongokit import Connection

DB_NAME = 'dict'

conn = Connection('127.0.0.1')
db = conn[DB_NAME]

users = db['users']  # 用户列表，包括管理员/编辑等
tokens = db['tokens'] # 最终的词库
sentences = db['sentences'] # 例句库
differences = db['differences'] # 辨析库

# 资源库 =====================================================
# 奇迹 ---------------------------------
qj_token_coll = db['resource.qiji.tokens']
qj_course_coll = db['resource.qiji.courses']
qj_sentence_coll = db['resource.qiji.sentences']

# dict.cn
dc_page_coll = db['resource.dictcn.pages']
dc_token_coll = db['resource.dictcn.tokens']
# dc_page_coll 来自网页抓取， 包含：
# segments, 音标， 常见度（5星），词形变换（注明词形）
# 中文解释+解释对应例句+例句中文解释
# 例句， 短语词组， 近反义词
# 海词讲解：词源解说、词义辨析、词语用法
# 英英解释（来自WordNet）

# 有道 ---------------------------------
yd_detail_page_coll = db['resource.youdao.detail_pages']
# yd_detail_page_coll 来自网页抓取，包含
# 英英解释（WordNet)；
# 英汉解释（有道简明），词形变换（注明词形）
# 英汉解释（21世纪）+例句&用法，词形变换（不注明词形）；
# 词组短语+解释
# 同近义词， 一个解释对应多个同近义词
# 科林斯词典，音标，segments，变形（不注明词形）；详细解释（词性，英文解释，中英例句）
# 同根词+本词的词根
# 图片
# 专业解释（各个领域）
# 有道网络词典
# 例句+翻译+来源URL,包括普通例句、发表物例句、多媒体例句
yd_21yh_page_coll = db['resource.youdao.21yh_pages']
# yd_21yh_page_coll 整个21世纪词典，包括：
# 英汉解释（21世纪）+例句&用法，词形变换（不注明词形）；
yd_simple_token_coll = db['resource.youdao.simple_tokens']

# collins ---------------------------------
cl_page_coll = db['resource.collins.pages']
cl_freq_page_coll = db['resource.collins.freq_pages']
cl_token_coll = db['resource.collins.tokens']

# wordnet ---------------------------------
wn_token_coll = db['resource.wordnet.tokens']