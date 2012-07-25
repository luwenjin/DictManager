# coding: utf-8
""" define all collections """
from _base import db

# 正式库 =====================================================
# 用户列表，包括管理员/编辑等
users = db['users']

# 词库
tokens = db['tokens']
tokens.ensure_index('en')

# 例句库
sentences = db['sentences']
sentences.ensure_index('include')

# 辨析库
diffs = db['diffs']

# 核心解释收集库
core_exp = db['core_exp']
core_exp.ensure_index('en')
core_exp.ensure_index('options.editor')
core_exp.ensure_index('options.voters')
core_exp.ensure_index('actions_count')
core_exp.ensure_index('tags')

# 分数库（记录核心解释的分数）
scores = db['scores']


# 资源库 =====================================================
# 奇迹 ---------------------------------
qj_token_coll = db['resource.qiji.tokens']
# en, exp, ph_en, ph_us, dict_word_id:qj内部唯一化id, word_id:qj内部流水id, course_id

qj_course_coll = db['resource.qiji.courses']
# id:qj的数字ID , name:ssb的内部英文ID, label:书名

qj_sentence_coll = db['resource.qiji.sentences']
# id, en, cn, include:对应这个句子的英文单词们

# dict.cn ---------------------------------
# dc_page_coll 来自网页抓取， 包含：
# segments, 音标， 常见度（5星），词形变换（注明词形）
# 中文解释+解释对应例句+例句中文解释
# 例句， 短语词组， 近反义词
# 海词讲解：词源解说、词义辨析、词语用法
# 英英解释（来自WordNet）
dc_page_coll = db['resource.dictcn.pages']
# en, content

dc_token_coll = db['resource.dictcn.tokens']
# en, seg（en的分段情况）, level（常见程度，5最高，1最低）， phs（音标列表）
# forms（词性：拼写）， exp_sentences（{exp:, sentences:{en:,cn:}})（解释所对应的例句）




# 有道 ---------------------------------
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
yd_detail_page_coll = db['resource.youdao.detail_pages']
# en, content

yd_21yh_page_coll = db['resource.youdao.21yh_pages']
# en, content
# yd_21yh_page_coll 整个21世纪词典，包括：
# 英汉解释（21世纪）+例句&用法，词形变换（不注明词形）；

yd_simple_token_coll = db['resource.youdao.simple_tokens']
# en, return_en, phs, speech, exps_cn, forms->[{type:, text:}], stem, rels->[{POS:, words->[{en:,cn:}]}]
yd_simple_token_coll.ensure_index('en')

# collins ---------------------------------
cl_page_coll = db['resource.collins.pages']
# en, content

cl_freq_page_coll = db['resource.collins.freq_pages']

cl_token_coll = db['resource.collins.tokens']
# en, current, band

# wordnet ---------------------------------
wn_token_coll = db['resource.wordnet.tokens']
# en, exps->[{POS, text, synset_token, count}]


# google translate# wordnet ---------------------------------
gt_token_coll = db['resource.google_translate.tokens']
# {en:, cn:}
gt_token_coll.ensure_index('en')