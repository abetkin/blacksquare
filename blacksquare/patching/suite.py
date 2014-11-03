import itertools
import operator
from functools import reduce

from ..util import PrototypeMixin, DotAccessDict, ContextAttribute
from .events import PatchSuiteStart, PatchSuiteFinish
from .base import HookWrapper, ReplacementWrapper, InsertionWrapper, Patch

class patch(DotAccessDict):
    '''
    Marks smth as a patch.

    Can decorate a function::

        @patch(**attrs)
        def marked_function(*a, **kw):
            pass

    or be assigned to an attribute::

        marked_attr = patch(**attrs)
    '''

    def make_patch(self):
        patch_type = self.get('patch_type', Patch)
        kwargs = {name: self[name] for name in self
                  if name in ('attribute', 'parent', 'wrapper_type')}
        return patch_type(prototype=self, **kwargs)

    def __call__(self, f):
        # decorate function
        self['wrapper_func'] = f
        self.setdefault('wrapper_type', ReplacementWrapper)
        return self

    @property
    def published_context(self):
        return (key for key in self.keys()
                if key not in ('attribute', 'parent', 'wrapper_type'))


class CollectPatchesMeta(type):

    def make_patches(cls, classdict):
        for name, value in classdict.items():
            if not isinstance(value, patch):
                continue
            p = value
            Meta = classdict.get('Meta', None)
            for attr, value in (Meta.__dict__.items()
                                if Meta else ()):
                if attr.startswith('__') and attr.endswith('__'):
                    continue
                p.setdefault(attr, value)
            p.setdefault('attribute', name)
            p.setdefault('wrapper_type', HookWrapper)
            yield p

    def __new__(cls, name, bases, classdict):
        patches = tuple(cls.make_patches(cls, classdict))
        classdict = {'collected_patches': patches,} # leave only this
        return type.__new__(cls, name, bases, classdict)


class BasePatchSuite:
    '''
    Container for patches.
    '''

    inherit_collected_patches = True

    def __init__(self, patches=()):
        if patches:
            self.patches = tuple(patches)
            return
        patch_marks = self.get_collected_patches()
        self.patches = tuple(p.make_patch() for p in patch_marks)


    @classmethod
    def get_collected_patches(cls):
        if not cls.inherit_collected_patches:
            return cls.collected_patches
        to_sum = (klass.__dict__.get('collected_patches', ())
                  for klass in reversed(cls.__mro__))
        return reduce(operator.add, to_sum)

    def __add__(self, other):
        patches = itertools.chain(iter(self), iter(other))
        return PatchSuite(patches)

    def __radd__(self, other):
        patches = itertools.chain(iter(other), iter(self))
        return PatchSuite(patches)

    def __iter__(self):
        return iter(self.patches)

    def __contains__(self, item):
        return item in self.patches

    def __getitem__(self, index):
        return self.patches[index]

    def __len__(self):
        return len(self.patches)

    def __enter__(self):
        PatchSuiteStart.emit(self)
        return self

    def __exit__(self, *exc_info):
        PatchSuiteFinish.emit(self)
        if exc_info[0]: # postmortem debug?
            raise

class PatchSuite(BasePatchSuite, metaclass=CollectPatchesMeta):
    pass
