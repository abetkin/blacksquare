# -*- coding: utf-8 -*-

import sys
import types

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


def is_classmethod(obj):
    if sys.version_info[0] == 2:
        # Python 2
        return (isinstance(obj, types.UnboundMethodType)
                and  isinstance(obj.__self__, type))
    # Python 3
    return (isinstance(obj, types.MethodType)
            and  isinstance(obj.__self__, type))
