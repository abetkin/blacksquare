import inspect
from ..core.threadlocal import ThreadLocalMixin
from ..core.events import Event

class CallRecord(object):
    '''
    Record about function call.
    '''

    def __init__(self, func, args, kwargs, rv):
        self.func = func
        sig = inspect.signature(func)
        self.call_args = sig.bind(*args, **kwargs)
        self.rv = rv
        Logger.instance().append(self)

class Logger(ThreadLocalMixin, list):
    pass

class FunctionExecuted(Event):
    pass

class ReplacementFunctionExecuted(FunctionExecuted):
    pass

class OriginalFunctionExecuted(FunctionExecuted):

    handlers = [CallRecord]
