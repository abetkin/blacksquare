from functools import wraps, partial
from types import MethodType
from .events import ReplacementFunctionExecuted, OriginalFunctionExecuted

from .. import get_config
from ..manage.events import ContextChange

# singledispatch ?

class Wrapper:

    def __init__(self, patch, wrapper_func, wrapped_func):
        self.patch = patch
        self.wrapped_func = wrapped_func
        self.wrapper_func = wrapper_func


    def execute(self):
        raise NotImplementedError()

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
    def _execute(self, *args, **kwargs):
        rv = self.wrapper_func(*args, **kwargs)
        ReplacementFunctionExecuted.emit(self, args, kwargs, rv)
        return rv


class InsertionWrapper(Wrapper):
    def _execute(self, *args, **kwargs):
        rv = self.wrapper_func(*args, **kwargs)
        ReplacementFunctionExecuted.emit(self, args, kwargs, rv)
        return rv


class Patch:

    parent = None

    def __init__(self, func, parent=None, wrapper_type=ReplacementWrapper,
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
        self.replacement = self._prepare_replacement(replacement, hook)

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
