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


class ParentContextMixin:

    PARENT_CONTEXT_ATTRIBUTE = '_parent_'
    GET_CONTEXT_METHOD = 'get_context'

    def _objects(self):
        obj = self
        while obj is not None:
            if hasattr(obj, self.GET_CONTEXT_METHOD):
                yield obj
            obj = getattr(obj, self.PARENT_CONTEXT_ATTRIBUTE, None)

    @property
    def context(self):
        ret = DotAccessDict()
        objects = list(self._objects())
        for obj in reversed(objects):
            get_context = getattr(obj, self.GET_CONTEXT_METHOD)
            ret.update(get_context())
        return ret

class ContextDict(dict):
    get_context = dict.items
