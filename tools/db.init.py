#coding:utf-8
import sqlite3
import random
import base64

from models import db, users, sentences
sql_conn = sqlite3.connect('ssb/resources/dicts/words.sqlite')

# making user collection
def init_users():
    for coll_name in db.collection_names():
        if coll_name.startswith('users'):
            db[coll_name].drop()
        if coll_name.startswith('tasks'):
            db[coll_name].drop()

    u1 = db.User()
    u1.sina_id = 1L
    u1.screen_name = u'test1'
    u1.save()

    u2 = db.User()
    u2.sina_id = 2L
    u2.screen_name = u'test2'
    u2.save()

    for user in db.User.find():
        print user


def drop_all_collection():
    for name in db.collection_names():
        if name == u'system.indexes':
            continue
        elif name.find('spy')>=0:
            continue
        db.drop_collection(name)
        print 'droped:', name

def import_barron_3500():
    name = u'SAT'
    label = u'SAT Barron3500词库'
    s = open('ssb/resources/dicts/WordList.Barron3500.db').read()

    old_course = courses.Course.find({'name':name})
    for course in old_course:
        course.delete()
    course = courses.Course()
    course.name = unicode(name)
    course.label = unicode(label)
    course.save()

    coll = courses[name]
    coll.drop()


    c = sql_conn.cursor()

    li = s.split('}')
    i = 0
    for block in li:

        lines = block.strip().split('\n')
        if len(lines)>3:
            foreign = lines[2].replace('[WordString]','').strip()
            pos = lines[3].replace('[PoSString]', '').strip()
            chinese = pos+lines[4].replace('[ChineseString]', '').strip()
            english = lines[5].replace('[EnglishString]', '').strip()
            sentence = lines[6].replace('[ExampleString]', '').strip()

            addition = lines[7].replace('[AdditionString]', '').strip()
            if english:
                chinese = english + '\n' + chinese
            if addition:
                chinese = chinese +'\n('+ addition +')'
            chinese = chinese.decode('utf-8')
            foreign = foreign.decode('utf-8')
            sentence = sentence.decode('utf-8')

            c.execute('select phonetic,phonetic_us,dict_word_id from dict_word where english=?',(foreign,))
            result = c.fetchone()

            phonetic = None
            phonetic_us = None
            dict_word_id = None
            if result:
                (phonetic, phonetic_us, dict_word_id) = result

            print foreign
            print phonetic, phonetic_us
            print '.'
            print chinese
            print '.'
            print sentence
            print '-----------------'

            i += 1
            word = coll.Word()
            word.foreign = foreign
            word.chinese = chinese
            word.language = u'en'
            word.phonetic = {}
            if phonetic:
                word.phonetic['en'] = phonetic
            if phonetic_us:
                word.phonetic['us'] = phonetic_us
            word.order = random.randint( 0, 2147483647 )
            word.dict_word_id = dict_word_id
            word.save()

            s = db.Sentence.find_one({'foreign':sentence})
            if not s:
                s = db.Sentence()
                s.foreign = sentence
                s.chinese = u'- Barron原版例句 -'
            if word.foreign not in s.word_list:
                s.word_list.append(word.foreign)
#            print  word.foreign, sentence.foreign
            s.save()

    course.word_count = i
    course.save()
            


def import_english_words(course_id, name, label, count=None):
    #get course info
    print 'import_words:', course_id, name, label
    c = sql_conn.cursor()
    c.execute('select course_name from course where course_id=?', (course_id,))

    #import words
    c.execute("select english,chinese,phonetic,phonetic_us,dict_word_id from wordinfo where course_id=?", (course_id,))

    old_course = courses.find({'name':name})
    for course in old_course:
        course.delete()

    course = courses.Course()
    course.name = unicode(name)
    course.label = unicode(label)
    course.save()

    coll = courses[name]
    coll.drop()

    i = 0
    for item in c.fetchall():
        if count and i>count:
            break
        i += 1
        word = coll.Word()
        word.foreign = unicode(item[0])
        word.chinese = unicode(item[1])
        word.language = u'en'
        word.phonetic = {}
        if item[2]:
            word.phonetic['en'] = unicode(item[2])
        if item[3]:
            word.phonetic['us'] = unicode(item[3])
        word.order = random.randint(0,2147483647)
        word.dict_word_id = item[4]
        word.save()
    course.word_count = i
    course.save()
    print 'import complete:', i


def import_english_sentences(course_name):
    #must import words first
    print 'import_sentences:', course_name
    word_coll = courses[course_name]
    c = sql_conn.cursor()
    
    for word in word_coll.Word.find():
        if not word.dict_word_id:
            continue
        c.execute('select sentence_id from word_sentence where dict_word_id=?',(word.dict_word_id,))
        r = c.fetchall()
        if not r:
            continue
        for item in r:
            sentence_id = item[0]

            c.execute('select english,chinese from sentence where sentence_id=?', (sentence_id,))
            r = c.fetchone()
            foreign = unicode(r[0])
            chinese = unicode(r[1])

            sentence = db.Sentence.find_one({'foreign':foreign})
            if not sentence:
                sentence = db.Sentence()
                sentence.foreign = foreign
                sentence.chinese = chinese
            if word.foreign not in sentence.word_list:
                sentence.word_list.append(word.foreign)
#            print  word.foreign, sentence.foreign
            sentence.save()


def import_differences():
    #must import words first
    print 'import_differences'
    
    c = sql_conn.cursor()
    c2 = sql_conn.cursor()
    c3 = sql_conn.cursor()
    c.execute('select id,word,discriminate from discriminate_details')

    differences.drop()
    
    for r in c.fetchall():
        details_id = r[0]
        word = unicode(r[1])
        meaning = r[2] #diff_meaning

        c2.execute('select discriminate_id from discriminate_relation where discriminate_details_id=?',(details_id,))
        for r2 in c2.fetchall():
            id = r2[0]
            c3.execute('select content from discriminate where id=?', (id,))
            same_meaning = unicode(c3.fetchone()[0])

            difference = differences.Difference.find_one({'same_meaning':same_meaning})
            if not difference:
                difference = differences.Difference()
                difference.same_meaning = same_meaning
                difference.diff_meanings = []
            if difference.diff_meanings == [] or word not in [x['word'] for x in difference.diff_meanings]:
                difference.diff_meanings.append({
                    'word':word,
                    'meaning':meaning,
                })
                difference.save()
                print 'SAVE:', word, meaning
            else:
#                print 'SKIP:', word,diff_meaning
                continue

        
def import_voices(course_name):
    import os
    import sys
    import shutil

    print sys.path

    for word in courses[course_name].Word.find():
        foreign = word.foreign
        source_dir = 'ssb/resources/voices/%s/mp3/' % word.language
        target_dir = 'ssb/static/voices/%s/mp3/' % word.language
        source_file_name = base64.urlsafe_b64encode(foreign.encode('utf-8'))+'.mp3'
        target_file_name = foreign+'.mp3'

#        print os.path.abspath(source_dir + source_file_name)

        source_path = os.path.abspath(source_dir + source_file_name)
        target_path = os.path.abspath(target_dir + target_file_name)
        
        if os.path.exists(target_path):
            print 'target already exist'
            word.has_voice = True
        elif os.path.exists(source_path):
            print 'source exists'
            try:
                shutil.copy(source_path, target_path)
            except:
                pass
            if os.path.exists(target_path):
                word.has_voice = True
            else:
                print 'fuck, copy failed'
                word.has_voice = False
        else:
            word.has_voice = False

        word.save()
        print word.foreign, word.has_voice


if __name__=='__main__':
#    drop_all_collection()
#    init_users()
#
#    import_english_words(173, 'GK', u'高考英语词汇必备')#高考
#    import_english_words(197, 'CET4',  u'大学英语四级')
#    import_english_words(198, 'CET6', u'大学英语六级')
#    import_english_words(209, 'YJS', u'研究生入学考试大纲词汇')#研究生
#
#    import_english_words(217, 'GRE', u'GRE核心词汇')
#    import_english_words(224, 'TOEFL', u'托福TOEFL核心词汇')
#    import_english_words(320, 'IELTS', u'雅思IELTS核心词汇')
#    import_english_words(212, 'GMAT', u'GMAT核心词汇')
#
#    import_english_sentences('GK')
#    import_english_sentences('CET4')
#    import_english_sentences('CET6')
#    import_english_sentences('YJS')
#    import_english_sentences('GRE')
#    import_english_sentences('TOEFL')
#    import_english_sentences('IELTS')
#    import_english_sentences('GMAT')
#
#    import_voices('GK')
#    import_voices('CET4')
#    import_voices('CET6')
#    import_voices('YJS')
#    import_voices('GRE')
#    import_voices('TOEFL')
#    import_voices('IELTS')
#    import_voices('GMAT')
#
#    import_differences()
#
#    import_english_words(198, 'TEST', u'大学英语六级(测试）', 20)
    import_barron_3500()
#    import_voices('SAT')
#    import_english_sentences('SAT')
#    import_differences()