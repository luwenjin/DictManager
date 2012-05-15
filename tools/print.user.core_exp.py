import sys
import os
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#------------------------------------------------------
from models import db, tokens, cl_token_coll, cl_page_coll, cl_freq_page_coll


editor_names = [ x for x in tokens.distinct('last_editor') if x ]
for editor_name in editor_names:
    time_li = []
    for token in tokens.Token.find({'last_editor': editor_name}, sort=[('modified_at', 1)]):
        modified_at = token.modified_at
        time_li.append(modified_at)
    interval_li = []
    for i in range(1, len(time_li)-1):
        time_begin = time_li[i]
        time_end = time_li[i+1]
        interval_li.append( int((time_end - time_begin).total_seconds()) )
    interval_li.sort()
    interval_li = [ x for x in interval_li if x < 120 ]
    if len(time_li)>80:
#        print editor_name
        print '%s\t%0.2f\t%s' % (
            len(time_li),
            sum(interval_li)/len(interval_li) if len(interval_li) else 0,
            editor_name,
            )
        for token in tokens.Token.find({'last_editor': editor_name}, sort=[('low', 1)]):
            print '\t\t\t%s\t%s' % (token.en, token.exp_core)
#        print interval_li
