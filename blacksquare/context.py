from functools import reduce

from .core.threadlocal import ThreadLocalMixin
from .patching.events import ContextChange

class DictAndObject(dict):
    def __init__(self, *args, **kw):
        super(DictAndObject, self).__init__(*args, **kw)
        self.__dict__ = self

class ContextTree(ThreadLocalMixin):

    global_name = 'context'

    def __init__(self):
        self._dict = DictAndObject()

    def __setitem__(self, name, value):
        ContextChange.emit(name)

        path = name.split('.')
        last_part = path.pop()
        obj = self._dict
        for part in path:
            obj = obj.setdefault(part, DictAndObject())
        obj[last_part] = value

    def __getitem__(self, name):
        path = name.split('.')
        return reduce(lambda x,y: x[y], path, self._dict)

