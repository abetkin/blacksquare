# -*- coding: utf-8 -*-
import collections

from IPython.lib import pretty

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


class _defaultdict(collections.defaultdict):
    def __contains__(self, elt):
        return True

class ObjectLookupPrinter(pretty.RepresentationPrinter):
    # falling back to _repr_pretty_

    lookup_attribute='_repr_pretty'

    def printer(self, obj, p, cycle):
        for cls in obj.__class__.__mro__:
            if self.lookup_attribute in cls.__dict__:
                meth = getattr(cls, self.lookup_attribute)
                if callable(meth):
                    return meth(obj, p, cycle)

    def __init__(self, *a, **kw):
        kw.pop('type_pprinters', None)
        type_pprinters = _defaultdict(lambda: self.printer)
        super().__init__(*a, type_pprinters=type_pprinters, **kw)


def pretty_custom(obj, printer_class=pretty.RepresentationPrinter,
                  verbose=False, max_width=79, newline='\n'):
    stream = pretty.StringIO()
    printer = printer_class(stream, verbose, max_width, newline)
    printer.pretty(obj)
    printer.flush()
    return stream.getvalue()

class DotAccessDict(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

class PrototypeChainCycle(Exception):
    def __init__(self, objects):
        message = ' -> '.join([str(obj) for obj in objects])
        super().__init__(message)


#class ContextAttribute(object):
#
#    def __get__()

def _context_attribute(name, *default):
    def fget(self):
        return self.get_from_context(name, *default)
    return property(fget)

ContextAttribute = _context_attribute # maybe sometimes will be a descriptor class


class PrototypeMixin:

    published_context = ()

    def _objects(self):
        # yields prototypes, detects cycles
        objects = []
        obj = self
        while obj is not None:
            yield obj
            obj = getattr(obj, '_parent_', None)
            if obj in objects:
                raise PrototypeChainCycle(objects)
            objects.append(obj)

    def get_from_context(self, attr, *default):
        for obj in self._objects():
            if attr in obj.published_context:
                return getattr(obj, attr)
        if not default:
            #import pdb; pdb.set_trace()

            raise AttributeError(attr)
        return default[0]

    def __init__(self, parent_obj=None):
        if parent_obj:
            self._parent_ = parent_obj

