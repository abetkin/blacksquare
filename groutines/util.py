# -*- coding: utf-8 -*-

import sys
import types

def object_from_name(name, module=None):
    """Import object from name"""
    parts = name.split('.')
    if module is None:
        parts_copy = parts[:]
        while parts_copy:
            try:
                module = __import__('.'.join(parts_copy))
                break
            except ImportError:
                del parts_copy[-1]
                if not parts_copy:
                    raise
        parts = parts[1:]

    obj = module
    
    if not parts:
        return None, None, obj
        
    for part in parts:
        parent, obj = obj, getattr(obj, part)
    return parent, part, obj

def is_classmethod(obj):
    if sys.version_info[0] == 2:
        # Python 2
        return (isinstance(obj, types.UnboundMethodType)
                and  isinstance(obj.__self__, type))
    # Python 3
    return (isinstance(obj, types.MethodType)
            and  isinstance(obj.__self__, type))
