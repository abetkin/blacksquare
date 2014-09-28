from functools import wraps
from types import MethodType
from .events import ReplacementFunctionExecuted, OriginalFunctionExecuted

class Patch:

    def __init__(self, parent, attribute, replacement=None, hook=None):
        self.parent = parent
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute)
        self.replacement = self.prepare_replacement(replacement, hook)

    def prepare_replacement(self, replacement=None, hook=None):
        # detach from __self__
        if hasattr(self.original, '__self__'):
            func = self.original.__func__
            __self__ = self.original.__self__
        else:
            func = self.original
            __self__ = None

         # make wrapper
        wrapper = Wrapper(self, func, replacement, hook)

        @wraps(func)
        def replacement(*args, **kw):
            return wrapper(*args, **kw)

        # attach back
        if isinstance(__self__, type):
            replacement = classmethod(replacement)
        elif __self__:
            replacement = MethodType(replacement, __self__)
        return replacement

    def on(self):
        setattr(self.parent, self.attribute, self.replacement)

    def off(self):
        setattr(self.parent, self.attribute, self.original)

    @property
    def is_on(self):
        return getattr(self.parent, self.attribute) != self.original


    def add_dependencies(self, *deps):
        '''
        on the context state
        '''
        self._deps = deps

    def get_dependencies(self):
        return getattr(self, '_deps', ())


class Wrapper:

    def __init__(self, patch, wrapped, replacement=None, hook=None):
        self.patch = patch
        self.wrapped = wrapped
        assert not (hook and replacement), ("You can define either "
                                            "hook or replacement")
        self.hook = hook
        self.replacement = replacement
        #TODO: __name__, __doc__

    def __str__(self):
        1

    def __call__(self, *args, **kwargs):
        #import ipdb; ipdb.set_trace()

        self.patch.off()
        try:
            if self.replacement:
                rv = self.replacement(*args, **kwargs)
                ReplacementFunctionExecuted.emit(self, args, kwargs, rv)
            else:
                rv = self.wrapped(*args, **kwargs)
                OriginalFunctionExecuted.emit(self, args, kwargs, rv)
            if self.hook:
                self.hook(*args, return_value=rv, **kwargs)
            return rv
        finally:
            self.patch.on()
        #log_call(self.wrapped, args, kwargs, rv)
        # manager-> default hooks: update deps


# to change
class Container:
    'Contains .patches'

    def __init__(self, patches=None):
        if patches:
            self.patches = patches

    def get_patches(self):
        return self.patches

