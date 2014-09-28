from collections import defaultdict
from functools import reduce

from ..core.threadlocal import ThreadLocalMixin


class ContextTree(ThreadLocalMixin):

    def __init__(self):

        def _tree():
            return defaultdict(_tree)

        self._tree = _tree()

    def __setitem__(self, name, value):
        from .events import ContextChange #FIXME
        ContextChange.emit(name)

        path = name.split('.')
        last = path.pop()
        if not path:
            parent = self._tree
        else:
            parent = reduce(lambda x,y: x[y], path, self._tree)
        parent[last] = value

    def __getitem__(self, name):
        path = name.split('.')
        value = reduce(lambda x,y: x[y], path, self._tree)
        if isinstance(value, defaultdict) and not value:
            raise KeyError(name)
        return value
