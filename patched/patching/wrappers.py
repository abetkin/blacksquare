from functools import wraps
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from ..util import PrototypeMixin, ContextAttribute


class Wrapper(PrototypeMixin):
    '''
    Base wrapper class. Usually subclasses just need to override the
    `.run()` method.

    Is responsible for making a wrapper callable with the same binding
    behavior as the wrapped callable has.

    The simplest use:

    >>> @Wrapper(wrapper_func=lambda *a, **k: "i'm a wrapper")
    ... def f(a, b):
    ...     return a + b
    ...
    >>> f(3, 5)
    "i'm a wrapper"
    '''

    wrapper_func = ContextAttribute('wrapper_func')

    pass_event = ContextAttribute('pass_event', False)
    event = ContextAttribute('event', None)

    published_context = ('wrapped_func',)

    def run(self, *args, **kwargs):
        if not self.pass_event:
            return self.wrapper_func(*args, **kwargs)
        return self.wrapper_func(*args, event=self.event, **kwargs)

    def __call__(self, wrapped):
        __self__ = getattr(wrapped, '__self__', None)
        if __self__:
             wrapped = wrapped.__func__
        self.wrapped_func = wrapped

        @wraps(wrapped or self.wrapper_func)
        def func(*args, **kwargs):
            patch = getattr(self, '_prototype_', None)
            if patch: patch.off()
            try:
                return self.run(*args, **kwargs)
            finally:
                if patch: patch.on()

        if isinstance(__self__, type):
            func = classmethod(func)
        elif __self__:
            func = MethodType(func, __self__)
        return func


class Replacement(Wrapper):
    event_class = ContextAttribute('event_class', ReplacementFunctionExecuted)

    def run(self, *args, **kwargs):
        self.event = self.event_class(args, kwargs, prototype=self)
        ret = super().run(*args, **kwargs)
        self.event.rv = ret
        # TODO: probably allow emit with args, update __dict__
        self.event.emit()
        return ret


class Insertion(Wrapper):
    pass


class Hook(Wrapper):
    event_class = ContextAttribute('event_class', HookFunctionExecuted)

    def run(self, *args, **kwargs):
        ret = self.wrapped_func(*args, **kwargs)
        self.event = self.event_class(args, kwargs, ret=ret, prototype=self)
        if self.get_from_context('wrapper_func', None):
            super().run(*args, return_value=ret, **kwargs)
        self.event.emit()
        return ret

