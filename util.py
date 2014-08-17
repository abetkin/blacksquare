# -*- coding: utf-8 -*-

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
