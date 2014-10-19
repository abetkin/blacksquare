from functools import wraps, partial
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from .. import get_config, get_context
from .events import ContextChange

class Wrapper:

    def __init__(self, patch, wrapper_func, wrapped=None):
        self.patch = patch
        self.wrapper_func = wrapper_func

        self.wrapped_func = wrapped
        self.__self__ = None
        if hasattr(wrapped, '__self__'):
            self.wrapped_func =  wrapped.__func__
            self.__self__ = wrapped.__self__
        # TODO: properties ?

        self.callable  = self._make_callable()

    def execute(self, *args, **kwargs):
        return self.wrapper_func(*args, **kwargs)

    def _execute(self, *args, **kwargs):
        self.patch.off()
        try:
            return self.execute(*args, **kwargs)
        finally:
            self.patch.on()

    def _make_callable(self):
        @wraps(self.wrapper_func)
        def func(*args, **kwargs):
            return self._execute(*args, **kwargs)

        if isinstance(self.__self__, type):
            func = classmethod(func)
        elif self.__self__:
            func = MethodType(func, self.__self__)
        return func


class ReplacementWrapper(Wrapper):
    def execute(self, *args, **kwargs):
        ret = self.wrapper_func(*args, **kwargs)
        ReplacementFunctionExecuted.emit(self, args, kwargs, ret)
        return ret


class InsertionWrapper(Wrapper):
    pass


class HookWrapper(Wrapper):
    def execute(self, *args, **kwargs):
        ret = self.wrapped_func(*args, **kwargs)
        self.wrapper_func(*args, return_value=ret, **kwargs)
        HookFunctionExecuted.emit(self, args, kwargs, ret)
        return ret

import itertools
from .events import PatchSuiteStart, PatchSuiteFinish


class PatchSuite:
    '''
    Container for patches.
    '''

    def __init__(self, *patches):
        self.patches = tuple(patches)

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


def patch(**kwargs):
    '''Mark function as a patch.'''
    def wrap(f):
        f.patch_kwargs = kwargs
        return f
    return wrap


class Patch:

    parent = None
    wrapper_type = ReplacementWrapper

    def __init__(self, attribute, wrapper_func, parent=None,
                 wrapper_type=None):
        if parent:
            self.parent = parent
        assert self.parent is not None, "parent can't be None"
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)

        wrapper_type = wrapper_type or self.wrapper_type
        self._wrapper = wrapper_type(self, wrapper_func=wrapper_func,
                                     wrapped=self.original)

    def on(self):
        setattr(self.parent, self.attribute, self.replacement)

    def off(self):
        if self.original:
            setattr(self.parent, self.attribute, self.original)
        else:
            delattr(self.parent, self.attribute)

    @property
    def replacement(self):
        return self._wrapper.callable

    @property
    def is_on(self):
        return getattr(self.parent, self.attribute) != self.original

    @classmethod
    def _make_patches(cls):
        for name, func in cls.__dict__.items():
            if not hasattr(func, 'patch_kwargs'):
                continue
            patch_kwargs = {'attribute': name, 'wrapper_func': func}
            patch_kwargs.update(func.patch_kwargs)
            yield cls(**patch_kwargs)

    @classmethod
    def make_patches(cls):
        return PatchSuite(*cls._make_patches())


# ugly, just a proof of concept
class SimpleConditionalPatch(Patch): # Enable
    event_to_listen = ContextChange

    def __init__(self, *args, **kw):
        super(SimpleConditionalPatch, self).__init__(*args, **kw)
        self._enabled = False
        get_config().register_event_handler(self.event_to_listen, self.enable)

    def on(self):
        if not self._enabled:
            return
        super(SimpleConditionalPatch, self).on()

    def enable(self, *args, **kw):
        Patch.on(self)
        self._enabled = True
        get_config().unregister_event_handler(self.event_to_listen,
                                              self.enable)
