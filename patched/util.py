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


def _fixed_context_attribute(name, *default):
    def fget(self):
        self.__dict__.setdefault('_context_attributes', {})
        if not self._context_attributes.get(name):
            value = self.get_from_context(name, *default)
            self._context_attributes[name] = value
        else:
            value = self._context_attributes[name]
        return value

    def fset(self, value):
        self.__dict__.setdefault('_context_attributes', {})
        self._context_attributes[name] = value

    return property(fget, fset)


def _dynamic_context_attribute(name, *default):
    def fget(self):
        return self.get_from_context(name, *default)

    return property(fget)

# Logically a descriptor, probably sometimes will turn into a descriptor class -
# hence the naming style.
def ContextAttribute(name, *default, fixed=True):
    if  fixed:
        return _fixed_context_attribute(name, *default)
    return _dynamic_context_attribute(name, *default)


class PrototypeMixin:

    published_context = ()

    def _objects(self):
        # yields prototypes, detects cycles
        objects = []
        obj = self
        while obj is not None:
            yield obj
            obj = getattr(obj, '_prototype_', None)
            if obj in objects:
                raise PrototypeChainCycle(objects)
            objects.append(obj)

    def get_from_context(self, attr, *default):
        for obj in self._objects():
            if attr in obj.published_context:
                return getattr(obj, attr)
            if hasattr(obj, 'published_context_extra') \
                    and attr in obj.published_context_extra:
                return obj.published_context_extra[attr]
        if default:
            return default[0]
        raise AttributeError(attr)


    def __init__(self, prototype=None):
        if prototype:
            self._prototype_ = prototype

