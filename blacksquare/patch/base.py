from functools import wraps
from types import MethodType
from .events import ReplacementFunctionExecuted, OriginalFunctionExecuted

class Patch:

    def __init__(self, parent, attribute,
                 replacement=None, hook=None,
                 insert=False, # to be able to create a patch that adds
                               # new attribute you should pass insert=True
                 ):
        self.parent = parent
        self.attribute = attribute
        try:
            self.original = getattr(self.parent, self.attribute)
        except AttributeError:
            assert insert
            self.original = None
        self._replacement_func = replacement
        self._hook_func = hook
        self.replacement = self.prepare_replacement(replacement, hook)


    def prepare_replacement(self, replacement=None, hook=None):
        # detach from __self__
        if hasattr(self.original, '__self__'):
            func = self.original.__func__
            __self__ = self.original.__self__
        #elif self.original.__class__.__name__ == 'property':
        #    #TODO: not read-only properties ?
        #    func = self.original.fget
        else:
            func = self.original
            __self__ = None

         # make wrapper
        wrapper = Wrapper(self, func, replacement, hook)

        @wraps(func)
        def replacement(*args, **kw):
            return wrapper(*args, **kw)

        # attach back #TODO: special insert=True case
        if isinstance(__self__, type):
            replacement = classmethod(replacement)
        elif __self__:
            replacement = MethodType(replacement, __self__)
        return replacement

    def on(self):
        setattr(self.parent, self.attribute, self.replacement)

    def off(self):
        if self.original:
            setattr(self.parent, self.attribute, self.original)
        else:
            delattr(self.parent, self.attribute)

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

    #def __str__(self):
    #    1

    def __call__(self, *args, **kwargs):
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
