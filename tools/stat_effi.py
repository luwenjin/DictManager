#coding:utf-8
import sys
import os
parent_path = os.path.split(os.path.split(os.path.abspath('.'))[0])[0]
print parent_path
sys.path.append(parent_path)
#-----------------------------------------------------------------
from datetime import datetime
from models import users
f = open('stat_effi.txt', 'w+')

BEGIN_TIME = datetime(2010, 9, 3)
END_TIME = datetime(2011, 9, 4)

def filter_by_span(uw, begin_time, end_time):
    history = uw.history
    uw.history = []
    for rec in history:
        if begin_time < rec['time'] < end_time:
            uw.history.append(rec)
    return uw

def is_mastered(uw):
    history_length = len(uw.history)
    if history_length < 3:
        return False
    else:
        for i in range(1,4):
            if uw.history[-i]['action'] != 'right':
                return False
        return True


for user in users.User.find():
    usercourse_list = user.usercourse_list
    for usercourse in usercourse_list:
        uw_coll = usercourse.userwords_collection

        mastered_words_count = 0
        step_count = 0
        for uw in uw_coll.UserWord.find():
            if uw.history[0]['action'] == 'right':
                continue
            else:
                uw = filter_by_span(uw, BEGIN_TIME, END_TIME)
                if is_mastered(uw):
                    mastered_words_count += 1
                    step_count += len(uw.history)


        line = u'%s\t%s\t%s/%s\t%s\n' % (
            user.screen_name,
            usercourse.name,
            mastered_words_count,
            step_count,
            int(1.0*mastered_words_count/step_count*100)/100.0 if step_count!=0 else 'None'
        )
        f.write(line.encode('utf-8'))
        print line,
f.close()
