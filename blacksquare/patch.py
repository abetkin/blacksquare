import inspect
from types import MethodType

from .log import Logger, CallRecord
from .events import ReplacementFunctionExecuted, OriginalFunctionExecuted


class Patch:

    def __init__(self, parent, attribute, hook=None, replacement=None):
        self.parent = parent
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute)
        self.replacement = self.prepare_replacement(hook, replacement)

    def prepare_replacement(self, hook=None, replacement=None):
        # detach from __self__
        __self__ = self.original.__self__
        func = self.original.__func__
         # make wrapper
        wrapper = Wrapper(self, func, hook, replacement)
        # attach back
        if isinstance(__self__, type):
            replacement = classmethod(wrapper)
        else:
            replacement = MethodType(wrapper, __self__)
        return replacement

    def on(self):
        setattr(self.parent, self.attribute, self.replacement)

    def off(self):
        setattr(self.parent, self.attribute, self.original)

    @property
    def is_on(self):
        return getattr(self.parent, self.attribute) != self.original



def log_call(wrapped, args, kwargs, rv):
    #TODO: customize logging to be usable not only for post-hooks
    #      but for custom replacement functions
    sig = inspect.signature(wrapped)
    call_args = sig.bind(*args, **kwargs)
    Logger.instance().append( CallRecord(call_args, rv))


class Wrapper:

    def __init__(self, patch, wrapped, hook=None, replacement=None):
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



class Container:
    'Contains .patches'

    def __init__(self, patches):
        self._patches = patches

    @property
    def patches(self):
        return self._patches

