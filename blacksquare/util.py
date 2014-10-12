# -*- coding: utf-8 -*-

import inspect
import string

def import_module(name):
    '''
    Import module and return a tuple (module, 'rest.of.the.path').
    '''
    parts = name.split('.')
    while parts:
        try:
            module = __import__('.'.join(parts))
            break
        except ImportError:
            del parts[-1]
            if not parts:
                raise

    return module, name.partition('.')[-1]

def import_obj(name):
    obj, path = import_module(name)
    for part in path.split('.'):
        parent = obj
        obj = getattr(parent, part)
    return parent, part, obj



class ObjectFormatter(string.Formatter):

    def get_value(self, key, args, kwds):
        if not isinstance(key, str):
            return string.Formatter.get_value(key, args, kwds)
        # this should be the context object
        value = args[0]

        for attr in key.split('.'):
            try:
                value = getattr(value, attr)
            except AttributeError as exc:
                try:
                    return value[attr]
                except (KeyError, TypeError):
                    raise exc
        return value

obj_formatter = ObjectFormatter()
