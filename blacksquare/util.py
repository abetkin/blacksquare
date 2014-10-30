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

class ParentObjectLookup:

    PARENT_CONTEXT_ATTRIBUTE = '_parent_'
    PUBLISH_TO_CONTEXT = 'publish_to_context'

    inject_context = False
    #publish_to_context = ()

    def __getattr__(self, attr):
        try:
            return super().__getattr__(attr)
        except AttributeError as ex:
            pass
        if self.inject_context:
            try:
                return self.get_from_context(attr)
            except AttributeError:
                pass
        raise ex

    def _objects(self):
        # detect cycles!
        obj = self
        while obj is not None:
            if hasattr(obj, self.PUBLISH_TO_CONTEXT):
                yield obj
            obj = getattr(obj, self.PARENT_CONTEXT_ATTRIBUTE, None)

    def get_from_context(self, attr, *default):
        obj = self
        while obj is not None:
            if attr in obj.publish_to_context:
                return getattr(obj, attr)
        if default == ():
            raise AttributeError(attr)
        return default[0]
    #
    #def __init__(self, *args, parent_obj=None, **kwargs):
    #    if parent_obj:
    #        self._parent_ = parent_obj
    #    super(ParentObjectLookup, self).__init__(self, *args, **kwargs)


class ContextDict(dict):
    get_context = dict.items
