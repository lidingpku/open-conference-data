# -*- coding: utf-8 -*-

import datetime
import collections
import copy
import json
import types


def json_default(obj):
    """Default JSON serializer."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
        return str(obj)


def json_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            if isinstance(value, types.StringTypes) and len(value) == 19 and value[4] == '-' and value[10] == 'T':
                json_dict[key] = datetime.datetime.strptime(
                    value, "%Y-%m-%dT%H:%M:%S")
        except Exception as e:
            print e
            pass
    return json_dict


def json2text(data):
    return json.dumps(data, indent=4, sort_keys=True, default=json_default, ensure_ascii=False, encoding='utf8')


def text2json(text, flag_use_hook=False):
    if None == text:
        return None
    else:
        if flag_use_hook:
            return json.loads(text, object_hook=json_hook)
        else:
            return json.loads(text)


def json_update(d, u, fields=None, flag_skip_null=False):
    if not isinstance(d, dict) or not isinstance(u, collections.Mapping):
        print "dict_update incompatible"
        return

    for k, v in u.iteritems():
        if None != fields and k not in fields:
            continue

        if flag_skip_null and v is None:
            continue

        if k not in d:
            d[k] = copy.deepcopy(v)
        else:
            if not isinstance(d[k], dict) and not isinstance(v, collections.Mapping):
                d[k] = v
            else:
                json_update(d[k], v)
    return d


def dict2list(json_dict, fields, default_value=""):
    """  for csv
        json_data = {"a1":"v1"}
        dict2list(json_data, ["a1","a2"], "")

        result is:
        [  "v1", ""]
    """
    ret = []
    for field in fields:
        if field in json_dict:
            ret.append(json_dict[field])
        else:
            ret.append(default_value)
    return ret


def dict_get(json_dict, list_field, default=None, flag_change_value=True):
    """
        json_data = {}
        dict_get(json_data, ["email","smtp","urls"],[])

        result is:
        {   "email": {
                "smtp": {
                    "urls": [],
                }
            }
        }
    """
    cur = json_dict
    for index, field in enumerate(list_field):
        if not isinstance(cur, dict):
            return None

        if field not in cur:
            if flag_change_value:
                if index == len(list_field) - 1:
                    #last one
                    cur[field] = default
                else:
                    cur[field] = {}
            else:
                return default

        cur = cur[field]

    return cur


def dict_is_true(data, key):
    return data and key in data and data[key]


def dict_is_equal(data1, data2, key):
    if key in data1 and key in data2:
        if data1[key] == data2[key]:
            return True
    return False


def list_unique(data):
    if isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, list):
        return sorted(list(set(data)))
    else:
        return None


def list_append_unique(list_data, item):
    if list_data is None:
        return
    if item is None:
        return

    if item in list_data:
        list_data.remove(item)
    list_data.append(item)