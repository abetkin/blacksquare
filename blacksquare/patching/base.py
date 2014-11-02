from functools import wraps, partial, update_wrapper
from types import MethodType
from .events import ReplacementFunctionExecuted, HookFunctionExecuted

from .. import get_config
from ..util import PrototypeMixin, ContextAttribute
from .events import ContextChange

#TODO test _bind to instance


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
    event_class = ContextAttribute('event_class', ReplacementFunctionExecuted)

    def run(self, *args, **kwargs):
        self.event = self.event_class(args, kwargs, parent_obj=self)
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
        self.event = self.event_class(args, kwargs, ret=ret, parent_obj=self)
        if self.get_from_context('wrapper_func', None):
            super().run(*args, return_value=ret, **kwargs)
        self.event.emit()
        return ret


class Patch(PrototypeMixin):

    parent = None

    wrapper_type = ContextAttribute('wrapper_type', ReplacementWrapper)

    def __init__(self, attribute, parent=None,
                 parent_obj=None, **kwargs):
        PrototypeMixin.__init__(self, parent_obj)
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
        self.wrapper = self.wrapper_type(parent_obj=self)(self.original)


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
    def _get_marks(cls):
        for name in dir(cls):
            value = getattr(cls, name)
            if callable(value) and hasattr(value, '_obj'):
                value._obj.update(wrapper_func=value)
                value._obj.setdefault('wrapper_type', ReplacementWrapper)
                value = value._obj
            if not isinstance(value, patch):
                continue
            yield name, value

    # This is a Patch factory
    @classmethod
    def _make_patches(cls):
        class_attributes = dict(cls._get_marks())
        #import ipdb; ipdb.set_trace()

        #for name in class_attributes:
        #    delattr(cls, name)
        for name, value in class_attributes.items():
            #if callable(value) and hasattr(value, '_obj'):
            #    value._obj.update(wrapper_func=value)
            #    value._obj.setdefault('wrapper_type', ReplacementWrapper)
            #    value = value._obj
            #if not isinstance(value, patch):
            #    continue
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
