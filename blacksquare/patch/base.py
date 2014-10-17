from functools import wraps, partial
from types import MethodType
from .events import ReplacementFunctionExecuted, OriginalFunctionExecuted

from .. import get_config
from ..manage.events import ContextChange
from ..manage.base import Patches

class Wrapper:

    def __init__(self, patch, wrapper_func, wrapped_func):
        self.patch = patch
        self.wrapped_func = wrapped_func
        self.wrapper_func = wrapper_func


    def execute(self, *args, **kwargs):
        return self.wrapper_func(*args, **kwargs)

    def _execute(self, *args, **kwargs):
        self.patch.off()
        try:
            return self.execute(*args, **kwargs)
        finally:
            self.patch.on()

    @property
    def function(self):
        return partial(self.__class__._execute, self=self)


class ReplacementWrapper(Wrapper):
    def execute(self, *args, **kwargs):
        rv = self.wrapper_func(*args, **kwargs)
        ReplacementFunctionExecuted.emit(self, args, kwargs, rv)
        return rv


class InsertionWrapper(Wrapper):

    def __init__(self, patch, wrapper_func):
        super(InsertionWrapper, self).__init__(patch, wrapper_func, None)


class HookWrapper(Wrapper):
    def execute(self, *args, **kwargs):
        rv = self.wrapped(*args, **kwargs)
        OriginalFunctionExecuted.emit(self, args, kwargs, rv)
        self.wrapper_func(*args, return_value=rv, **kwargs)


def patch(**kwargs):
    '''Mark function as a patch.'''
    def wrap(f):
        f.patch_kwargs = kwargs
        return f
    return wrap


#TODO: patch as container
class Patch:

    parent = None
    wrapper_type = ReplacementWrapper

    def __init__(self, attribute, wrapper_func, parent=None,
                 wrapper_type=None):
        if parent:
            self.parent = parent
        assert parent is not None, "parent can't be None"
        self.parent = parent
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)

        wrapper_type = wrapper_type or self.wrapper_type
        self.wrapper = wrapper_type(self, wrapper_func=wrapper_func,
                                    wrapped_func=self.original)

    @property
    def replacement(self):
        return self.wrapper.function

    '''
    def _prepare_replacement(self, replacement=None, hook=None):
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
    '''

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

    @classmethod
    def _make_instances(cls):
        for name, func in cls.__dict__.items():
            if name.startswith('__'):
                continue
            if not hasattr(func, '__call__'):
                continue
            patch_kwargs = {'attribute': name, 'wrapper_func': func}
            patch_kwargs.update( getattr(func, 'patch_kwargs', ()))
            yield cls(**patch_kwargs)

    @classmethod
    def make_instances(cls):
        return Patches(*cls._make_instances())


#class ConditionalPatch(Patch):
#
#    def is_ready(self):
#        raise NotImplementedError()
#
#    event_to_listen = ContextChange
#
#    # enabled / disabled ?
#
#    def on(self):
#        if self.is_ready():
#            Patch.on(self)
#        else:
#            get_config().register_event_handler(self.event_to_listen,
#                                                self.handler)
#
#    def handler(self):
#        if self.is_ready():
#            Patch.on(self)
#            get_config().unregister_event_handler(self.event_to_listen,
#                                                  self.handler)

class SimpleConditionalPatch(Patch):
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
