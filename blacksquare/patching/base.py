from functools import wraps, partial, update_wrapper
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from .. import get_config, get_context
from ..util import ParentContextMixin, DotAccessDict
from .events import ContextChange

#TODO test _bind to instance

#mixin?
class Wrapper:

    def __init__(self, patch, wrapper_func, wrapped=None):
        self.patch = patch
        self.wrapper_func = wrapper_func

        self.wrapped_func = self._unbind(wrapped)
        # TODO: properties ?

        self._execute = self.build()
        self.callable = self._bind(self._execute) # make it 1 attribute

    def execute(self, *args, **kwargs):
        return self.wrapper_func(*args, **kwargs)


    # property: wrapper
    def build(self):
        '''Build the wrapper function.'''
        @wraps(self.wrapped_func or self.wrapper_func) # -> _exe
        def func(*args, **kwargs):
            self.patch.off()
            try:
                return self.execute(*args, **kwargs)
            finally:
                self.patch.on()
        return func

    def _unbind(self, callabl):
        func = callabl
        self.__self__ = None
        if hasattr(callabl, '__self__'):
            func =  callabl.__func__
            self.__self__ = callabl.__self__
        return func

    def _bind(self, func):
        if isinstance(self.__self__, type):
            func = classmethod(func)
        elif self.__self__:
            func = MethodType(func, self.__self__)
        return func

    @property
    def instance(self):
        1


class ReplacementWrapper(Wrapper):

    def execute(self, *args, **kwargs):
        ret = self.wrapper_func(*args, **kwargs)
        ReplacementFunctionExecuted.emit(self, args, kwargs, ret)
        return ret


class InsertionWrapper(Wrapper):
    pass


class HookWrapper(Wrapper):

    def __init__(self, patch, wrapper_func=None, wrapped=None):
        super().__init__(patch, wrapper_func, wrapped)

    def execute(self, *args, **kwargs):
        ret = self.wrapped_func(*args, **kwargs)
        if self.wrapper_func:
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

# TODO: make kwargs set attributes on wrapper
class patch(dict):
    '''Mark function as a patch.'''

    def __call__(self, f):
        f._obj = self
        return f

    def get_context(self):
        import ipdb; ipdb.set_trace()

        return {key: self[key] for key in self
                if key not in ('attribute', 'parent', 'replacement')}

def default_replacement(ctx, *args, **kwargs):
    ret = ctx.wrapper_func(*args, **kwargs)
    ReplacementFunctionExecuted.emit(ctx.wrapper_func, args, kwargs, ret)
    return ret


class Patch(ParentContextMixin):

    parent = None
    #wrapper_type = ReplacementWrapper

    def __init__(self, attribute, parent=None,
                 replacement=default_replacement, **kwargs):
        if parent:
            self.parent = parent
        assert self.parent is not None, "parent can't be None"
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)
        #
        #wrapper_type = wrapper_type or self.wrapper_type
        #self._wrapper = wrapper_type(self, wrapper_func=wrapper_func,
        #                             wrapped=self.original)
        self.wrapper = partial(replacement, self.context)

        self._kwargs = kwargs

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
                      if name in ('attribute', 'parent', 'replacement')}
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
