from functools import wraps, partial, update_wrapper
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from .. import get_config
from ..util import PrototypeMixin, ContextAttribute
from .events import ContextChange


class Wrapper(PrototypeMixin):

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
            patch = self._prototype_
            patch.off()
            try:
                return self.run(*args, **kwargs)
            finally:
                patch.on()

        if isinstance(__self__, type):
            func = classmethod(func)
        elif __self__:
            func = MethodType(func, __self__)
        return func


class ReplacementWrapper(Wrapper):
    event_class = ContextAttribute('event_class', ReplacementFunctionExecuted)

    def run(self, *args, **kwargs):
        self.event = self.event_class(args, kwargs, prototype=self)
        ret = super().run(*args, **kwargs)
        self.event.rv = ret
        # TODO: probably allow emit with args, update __dict__
        self.event.emit()
        return ret


class InsertionWrapper(Wrapper):
    pass


class HookWrapper(Wrapper):
    event_class = ContextAttribute('event_class', HookFunctionExecuted)

    def run(self, *args, **kwargs):
        ret = self.wrapped_func(*args, **kwargs)
        self.event = self.event_class(args, kwargs, ret=ret, prototype=self)
        if self.get_from_context('wrapper_func', None):
            super().run(*args, return_value=ret, **kwargs)
        self.event.emit()
        return ret


class Patch(PrototypeMixin):

    parent = None

    wrapper_type = ContextAttribute('wrapper_type', ReplacementWrapper)

    def __init__(self, attribute, parent=None,
                 prototype=None, **kwargs):
        PrototypeMixin.__init__(self, prototype)
        if kwargs:
            # alternative to specifying parent object
            self.published_context_extra = dict(
                getattr(self, 'published_context_extra', ()),
                **kwargs)
        if parent:
            self.parent = parent
        assert self.parent is not None, "parent can't be None"
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)
        self.wrapper = self.wrapper_type(prototype=self)(self.original)


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

    def __repr__(self):
        # TODO
        try:
            return "Patch %s.%s" % (self.parent.__name__, self.original.__name__)
        except:
            return super().__repr__()

# ugly, just a proof of concept
class SimpleConditionalPatch(Patch):

    listen_to = ContextAttribute('listen_to', ContextChange)

    def __init__(self, *args, **kw):
        super(SimpleConditionalPatch, self).__init__(*args, **kw)
        self._enabled = False
        get_config().register_event_handler(self.listen_to, self.enable)

    def on(self):
        if not self._enabled:
            return
        super(SimpleConditionalPatch, self).on()

    def enable(self, *args, **kw):
        Patch.on(self)
        self._enabled = True
        get_config().unregister_event_handler(self.listen_to, self.enable)
