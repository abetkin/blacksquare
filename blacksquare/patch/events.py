import os
import inspect
import string

from ..core.threadlocal import ThreadLocalMixin
from ..core.events import Event
from ..config.core import Config

#TODO add record_class to config
class CallRecord(object):
    '''
    Record about function call.
    '''

    def __init__(self, wrapper, args, kwargs, rv):
        self.wrapper = wrapper
        sig = inspect.signature(wrapper)
        self.call_args = sig.bind(*args, **kwargs)
        self.rv = rv

    @property
    def log_record_format(self):
        if self.wrapper.replacement:
            return ("Call to {wrapper.wrapped.__name__} ( => "
                    "{wrapper.patch._replacement_func.__name__})")

        return ("Call to {wrapper.wrapped.__name__} ( + "
                "{wrapper.patch._hook_func.__name__})")

    def __str__(self):
        from ..util import formatter
        return formatter.format(self.log_record_format, self)



class Logger(ThreadLocalMixin, list):
    global_name = 'logger'

    def __str__(self):
        return os.linesep.join(str(record) for record in self)

    __repr__ = __str__


class EmbedShellHandler(object):
    @classmethod
    def handle(cls, wrapper, args, kwargs, rv):
        config = Config.instance()
        if config.is_set_bp_for(wrapper):
            from ..manage.context import ContextTree
            ctx = ContextTree()
            if config.test_interactive:
                config.test_interactive(ctx)
                return
            try:
                assert config.use_ipython
                import IPython
                IPython.embed()
            except (ImportError, AssertionError):
                import code
                code.interact(local={'ctx': ctx})

class FunctionExecuted(Event):

    @classmethod
    def get_handlers(cls):
        return (cls, EmbedShellHandler)

    @classmethod
    def handle(cls, wrapper, args, kwargs, rv):
        record = CallRecord(wrapper, args, kwargs, rv)
        Logger.instance().append(record)



class ReplacementFunctionExecuted(FunctionExecuted):
    pass

class OriginalFunctionExecuted(FunctionExecuted):
    pass

