from ._base import conn, db, users, differences, sentences, tokens, \
    qj_token_coll, qj_course_coll, qj_sentence_coll, \
    dc_page_coll, dc_token_coll, \
    yd_detail_page_coll, yd_simple_token_coll, yd_21yh_page_coll, \
    cl_page_coll, cl_freq_page_coll, cl_token_coll, \
    wn_token_coll

from .user import User
from .difference import Difference
from .sentence import Sentence
from .token import Token
from .resources import QJCourse, QJSentence, QJToken, DCPage, DCToken, YDSimpleToken, CLToken, Page, WNToken

conn.register([
    User,
    Difference,
    Sentence,
    Token,

    QJCourse,
    QJSentence,
    QJToken,

    DCPage,
    DCToken,

    YDSimpleToken,

    CLToken,

    WNToken,

    Page,
])