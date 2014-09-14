# -*- coding: utf-8 -*-

from functools import reduce, wraps
import six

from util import is_classmethod, import_obj
from local import get_tree



class Patch(object):
    '''
    Record about function to be patched
    '''

    #dependencies = ['a.b', 'a.bb']
    #path = 'a.b.c'

    #TODO: condition, dep. condition

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

        self.dependencies = []
        self.patched = False

    #XXX
    def check_deps(self):
        for dep in self.dependencies:
            tree = get_tree()
            path = dep.split('.')
            for name in path:
                if name not in tree:
                    return False
                tree = tree[name]
        return True

    def handle_return(self, value):
        tree = get_tree()
        path = self._path.split('.')
        last = path.pop()
        if not path:
            parent = tree
        else:
            parent = reduce(lambda x,y: x[y], path, tree)
        parent[last] = value

    def patch(self):
        '''
        Replace original with wrapper.
        '''
        #if is_classmethod(self._target):
        #    target = classmethod(self._target.__func__)
        #else:
        target = self._target
        setattr(self._target_parent, self._target_attribute, self(target))
        self.patched = True
    
    def restore(self):
        '''
        Put original callable on it's place back.
        '''
        setattr(self._target_parent, self._target_attribute, self._target)
        self.patched = False

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
            self.handle_return(rv)
            return rv

        wrapper.__name__ = wrapped.__name__
        return wrapper


class PatchManager(object):

    def __init__(self, *records):
        self.records = records

    def __enter__(self):
        for thing in self.records:
            thing.patch()

    def __exit__(self, *exc_info):
        if exc_info[0]: #XXX
            raise
        for thing in self.records:
            thing.restore()

if __name__ == '__main__':

    class SomeClass(object):

        def __init__(self):
            self.a = 1

        def start(self):
            return 1

        @classmethod
        def middle(cls, default=2):
            return default

        def end(self):
            return 1

    pm = PatchManager(
        Patch('__main__.SomeClass.middle'),
    )

    o = SomeClass()
    with pm:
        print( SomeClass.middle(default=6))

