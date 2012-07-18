#coding: utf-8
from datetime import datetime

import json as simplejson

from flask import current_app, request
from mongokit import ObjectId


def today():
    t = datetime.now()
    return get_day_begin(t)

def get_day_begin(t):
    return datetime(t.year, t.month, t.day)

def to_time_string(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_seconds_from_timedelta(td):
    return td.days*24*3600 + td.seconds + td.microseconds/1000000.0

def avg(list_of_numbers):
    return 1.0*sum(list_of_numbers)/len(list_of_numbers)


class SSBJSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if type(o) == datetime:
            return to_time_string(o)
        elif type(o) == ObjectId:
            return str(o)
        else:
            return simplejson.JSONEncoder.default(self, o)

    def encode(self, o, indent=None):
        if indent:
            self.indent = ' ' * indent
        return simplejson.JSONEncoder.encode(self, o)


json_encoder = SSBJSONEncoder()




