# -*- coding: utf-8 -*-

import inspect
from functools import reduce, wraps
import six

from .util import is_classmethod, import_obj
from .local import tlocal, Tree, Logger

class Patch:
    '''
    Record about function to be patched
    '''

    def __init__(self, target, path=None, replacement=None):
        '''
        target: str or (container, 'attribute')
        path: path to store in a tree. Defaults to function name.
        '''
        if isinstance(target, six.string_types):
            self._target_parent, self._target_attribute, self._target = \
                    import_obj(target)
        else:
            self._target_parent, self._target_attribute = target
            self._target = getattr(self._target_parent, self._target_attribute)

        self._replacement = wraps(self._target)(replacement) \
                            if replacement else None
        self._path = path or self._target.__name__

        self.deps = []
        self.patched = False

    def log_call(self, wrapped, args, kwargs, rv):
        #TODO: customize logging to be usable not only for post-hooks
        #      but for custom replacement functions
        sig = inspect.signature(wrapped)
        call_args = sig.bind(*args, **kwargs)
        Logger.instance().append( CallRecord(call_args, rv))

    def patch(self):
        '''
        Replace original with wrapper.
        '''
        target = self._target
        setattr(self._target_parent, self._target_attribute, self(target))
        self.patched = True
    
    def restore(self):
        '''
        Put original callable on it's place back.
        '''
        setattr(self._target_parent, self._target_attribute, self._target)
        self.patched = False

    def check_ready(self):
        #TODO: custom conditions
        for dep in self.deps:
            if dep not in Tree.instance:
                break
        else:
            return True

    def __call__(self, wrapped):
        # For PY3 we can use simple decorator as a wrapper,
        # since methods accessed from class are just regular functions.

        # for PY2 we can use wrapt.WeakFunctionProxy.

        def wrapper(*args, **kwargs):
            self.restore()
            try:
                if self._replacement:
                    rv = self._replacement(wrapped, *args, **kwargs)
                else:
                    rv = wrapped(*args, **kwargs)
            finally:
                self.patch()
            self.log_call(wrapped, args, kwargs, rv)
            return rv

        wrapper.__name__ = wrapped.__name__
        return wrapper

from itertools import groupby

class PatchManager: # 1

    def __init__(self, *records):
        self.records_no_deps = [rec for rec in records
                                if not rec.has_deps()]
        self.records_with_deps = [rec for rec in records
                                  if rec not in self.records_no_deps]

    @classmethod
    def instance(cls):
        if not hasattr(tlocal, 'manager'):
            tlocal.manager = cls()
        return tlocal.manager

    def patch_all(self):
        for thing in self.records:
            thing.patch()

    def restore_all(self):
        for thing in (self.records_no_deps + self.records_with_deps):
            thing.restore()

    def new_value_in_context(self, name):
        for record in self.records_with_deps:
            if name not in record.deps:
                return
            if record.check_ready():
                record.patch()


    #

    def __enter__(self):
        self.patch_all()

    def __exit__(self, *exc_info):
        if exc_info[0]: #XXX
            raise
        self.restore_all()


class CallRecord(object):
    '''
    Record about function call.
    '''

    def __init__(self, call_args, rv):
        self.call_args = call_args
        self.rv = rv


#if __name__ == '__main__':
#
#    class SomeClass:
#
#        def __init__(self):
#            self.a = 1
#
#        def start(self):
#            return 1
#
#        @classmethod
#        def middle(cls, default=2):
#            return default
#
#        def end(self):
#            return 1
#
#    pm = PatchManager(
#        Patch('__main__.SomeClass.middle'),
#    )
#
#    o = SomeClass()
#    with pm:
#        print( SomeClass.middle(default=6))

