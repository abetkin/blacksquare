from collections import defaultdict
from functools import reduce

from .base import ThreadLocalMixin
from ..events import ContextChange

class ContextTree(ThreadLocalMixin):

    def __init__(self):

        def _tree():
            return defaultdict(_tree)

        self._tree = _tree()

    def __setitem__(self, name, value):
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


class PatchManager(ThreadLocalMixin):

    global_name = 'manager'

    def __init__(self, config):
        # .
        self.records_no_deps = []
        self.records_with_deps = []

    def add_patches(self, *records):
        self.records_no_deps = [rec for rec in records
                                if not rec.deps]
        self.records_with_deps = [rec for rec in records
                                  if rec not in self.records_no_deps]


    def patch_all(self):
        for thing in self.records_no_deps:
            thing.patch()

    def restore_all(self):
        for thing in self.records_no_deps + self.records_with_deps:
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

