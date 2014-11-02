import itertools

from ..util import PrototypeMixin, DotAccessDict, ContextAttribute
from .events import PatchSuiteStart, PatchSuiteFinish
from .base import HookWrapper, ReplacementWrapper, InsertionWrapper, Patch

# parent_obj -> prototype

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

    def make_patch(self, attribute):
        patch_type = self.get('patch_type', Patch)
        self.setdefault('attribute', attribute)
        self.setdefault('wrapper_type', HookWrapper)
        kwargs = {name: self[name] for name in self
                  if name in ('attribute', 'parent', 'wrapper_type')}
        return patch_type(parent_obj=self, **kwargs)

    def __call__(self, f):
        # decorate function
        self.wrapper_func = f
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
            import ipdb; ipdb.set_trace()
            p = value
            Meta = classdict.get('Meta', None)
            for name, value in (Meta.__dict__.items()
                                if Meta else ()):
                if name.startswith('__') and name.endswith('__'):
                    continue
                p.setdefault(name, value)
            obj = p.make_patch(name)
            yield obj

    def __new__(cls, name, bases, classdict):
        # drop classdict
        classdict = {
            'patches': tuple(cls.make_patches(cls, classdict)),
        }
        return type.__new__(cls, name, bases, classdict)



class PatchSuite(metaclass=CollectPatchesMeta
                 ):
    '''
    Container for patches.
    '''

    #class Meta:
    #    parent =

    def __init__(self, patches=()):
        if patches:
            self.patches = tuple(patches)
        # else: will use collected from class declaration

    def __add__(self, other):
        patches = itertools.chain(iter(self), iter(other))
        return PatchSuite(*patches)

    def __radd__(self, other):
        patches = itertools.chain(iter(other), iter(self))
        return PatchSuite(*patches)

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

#
#class patch(DotAccessDict):
#    '''
#    Marks smth as a patch.
#
#    Can decorate a function::
#
#        @patch(**attrs)
#        def marked_function(*a, **kw):
#            pass
#
#    or be assigned to an attribute::
#
#        marked_attr = patch(**attrs)
#    '''
#
#    def make_patch(self, attribute):
#        patch_type = self.get('patch_type', Patch)
#        self.setdefault('attribute', attribute)
#        self.setdefault('wrapper_type', HookWrapper)
#        kwargs = {name: self[name] for name in self
#                  if name in ('attribute', 'parent', 'wrapper_type')}
#        return patch_type(parent_obj=self, **kwargs)
#
#    def __call__(self, f):
#        # decorate function
#        self.wrapper_func = f
#        self.setdefault('wrapper_type', ReplacementWrapper)
#        return self
#
#    @property
#    def published_context(self):
#        return (key for key in self.keys()
#                if key not in ('attribute', 'parent', 'wrapper_type'))
#
