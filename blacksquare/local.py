
import threading

from collections import defaultdict
from functools import reduce


tlocal = threading.local()

#def get_tree():



class CallRecord(object):
    '''
    Record about function call.
    '''

    def __init__(self, ):
        pass


class Tree(object):
    '''Context tree.'''

    def __init__(self):

        def _tree():
            return defaultdict(_tree)

        self._tree = _tree()

    @classmethod
    def instance(cls):
        if not hasattr(tlocal, 'tree'):
            tlocal.tree = cls()
        return tlocal.tree

    def get_patch_manager(self):
        from .core import PatchManager
        return PatchManager.instance()

    def __setitem__(self, name, value):
        self.get_patch_manager().new_value_in_context(name)

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

