from functools import wraps, partial, update_wrapper
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from .. import get_config, get_context
from ..util import PrototypeMixin, DotAccessDict, ContextAttribute
from .events import ContextChange

#TODO test _bind to instance

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


class patch(DotAccessDict):
    '''Mark function as a patch.'''

    def __call__(self, f):
        f._obj = self
        return f

    @property
    def published_context(self):
        return (key for key in self.keys()
                if key not in ('attribute', 'parent', 'wrapper_type'))


class Wrapper(PrototypeMixin):

    wrapper_func = ContextAttribute('wrapper_func')

    published_context = ('wrapped_func',)

    @property
    def patch(self):
        return self._parent_

    def run(self, *args, **kwargs):
        return self.wrapper_func(*args, **kwargs)


    def __call__(self, wrapped):
        __self__ = getattr(wrapped, '__self__', None)
        if __self__:
             wrapped = wrapped.__func__
        self.wrapped_func = wrapped

        @wraps(wrapped or self.wrapper_func)
        def func(*args, **kwargs):
            patch = self._parent_
            patch.off()
            try:
                return self.run(*args, **kwargs)
            finally:
                patch.on()

        if isinstance(__self__, type):
            func = classmethod(func)
        elif __self__:
            func = MethodType(func, self.__self__)
        return func


class ReplacementWrapper(Wrapper):
    def run(self, *args, **kwargs):
        ret = self.wrapper_func(*args, **kwargs)
        event = ReplacementFunctionExecuted(args, kwargs, ret, parent_obj=self)
        event.emit()
        return ret


class InsertionWrapper(Wrapper):
    pass


class HookWrapper(Wrapper):
    def run(self, *args, **kwargs):
        ret = self.wrapped_func(*args, **kwargs)
        if self.get_from_context('wrapper_func', None):
            self.wrapper_func(*args, return_value=ret, **kwargs)
        event = HookFunctionExecuted(args, kwargs, ret=ret, parent_obj=self)
        event.emit()
        return ret


class Patch(PrototypeMixin):

    parent = None

    def __init__(self, attribute, parent=None, wrapper_type=ReplacementWrapper,
                 parent_obj=None, **kwargs):
        PrototypeMixin.__init__(self, parent_obj)
        if parent:
            self.parent = parent
        assert self.parent is not None, "parent can't be None"
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)
        self.wrapper_type = wrapper_type
        self.wrapper = wrapper_type(parent_obj=self)(self.original)
        self._kwargs = kwargs      # unlikely to be used

    @property
    def published_context(self):
        if '_kwargs' in self.__dict__:
            return self._kwargs.keys() # unlikely to be used
        return ()

    def __getattr__(self, name):   # unlikely to be used
        if '_kwargs' in self.__dict__:
            return self._kwargs[name]
        raise AttributeError(name)

    def on(self):
        setattr(self.parent, self.attribute, self.wrapper)

    def off(self):
        if self.original:
            setattr(self.parent, self.attribute, self.original)
        else:
            delattr(self.parent, self.attribute)

    @property
    def is_on(self):
        return getattr(self.parent, self.attribute) != self.original

    # This is a Patch factory
    # TODO: probably make customizable
    @classmethod
    def _make_patches(cls):
        for name, value in cls.__dict__.items():
            if callable(value) and hasattr(value, '_obj'):
                value._obj.update(wrapper_func=value)
                value._obj.setdefault('wrapper_type', ReplacementWrapper)
                value = value._obj
            if not isinstance(value, patch):
                continue
            value.setdefault('attribute', name)
            value.setdefault('wrapper_type', HookWrapper)
            kwargs = {name: value[name] for name in value
                      if name in ('attribute', 'parent', 'wrapper_type')}
            obj = cls(parent_obj=value, **kwargs)
            yield obj

    @classmethod
    def make_patches(cls):
        patches = list(cls._make_patches())
        return PatchSuite(*patches)


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
