from functools import wraps, partial, update_wrapper
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from .. import get_config, get_context
from ..util import ParentContextMixin, DotAccessDict
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

# TODO: make kwargs set attributes on wrapper
class patch(dict):
    '''Mark function as a patch.'''

    def __call__(self, f):
        f._obj = self
        return f

    def get_context(self):
        #import ipdb; ipdb.set_trace()

        return {key: self[key] for key in self
                if key not in ('attribute', 'parent', 'wrapper')}

def default_wrapper(ctx, *args, **kwargs):
    ret = ctx.wrapper_func(*args, **kwargs)
    ReplacementFunctionExecuted.emit(ctx.wrapper_func, args, kwargs, ret)
    return ret

def insertion_wrapper(ctx, *args, **kwargs):
    return ctx.wrapper_func(*args, **kwargs)

def hook_wrapper(ctx, *args, **kwargs):
    ret = ctx.wrapped_func(*args, **kwargs)
    if ctx.wrapper_func:
        ctx.wrapper_func(*args, return_value=ret, **kwargs)
    HookFunctionExecuted.emit(ctx.wrapper_func, args, kwargs, ret)
    return ret


class Patch(ParentContextMixin):

    parent = None
    #wrapper_type = ReplacementWrapper

    def __init__(self, attribute, parent=None, wrapper=default_wrapper,
                 **kwargs):
        if parent:
            self.parent = parent
        assert self.parent is not None, "parent can't be None"
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)
        #
        #wrapper_type = wrapper_type or self.wrapper_type
        #self._wrapper = wrapper_type(self, wrapper_func=wrapper_func,
        #                             wrapped=self.original)
        self._kwargs = kwargs
        self.wrapper = partial(wrapper, self.context)



    def get_context(self):
        return self._kwargs # usually {}

    @property
    def wrapper(self):
        return self._wrapper

    #def _signature_f(self):1

    @wrapper.setter
    def wrapper(self, function):
        context = self.context

        __self__ = getattr(function, '__self__', None)
        if __self__:
            function = function.__func__

        @wraps(context.get('wrapped_func') or context.wrapper_func)
        def func(*args, **kwargs):
            self.off()
            try:
                return function(*args, **kwargs)
            finally:
                self.on()

        if isinstance(__self__, type):
            func = classmethod(func)
        elif __self__:
            func = MethodType(func, self.__self__)
        self._wrapper = func

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

    @classmethod
    def _make_patches(cls):
        for name, value in cls.__dict__.items():
            if callable(value) and hasattr(value, '_obj'):
                value._obj.update(wrapper_func=value)
                value = value._obj
            if not isinstance(value, patch):
                continue
            kwargs = {name: value[name] for name in value
                      if name in ('attribute', 'parent', 'wrapper')}
            obj = cls(**kwargs)
            obj._parent_ = value
            yield obj

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
