
from .threadlocal import Config
from . import handlers

class Event:

    handlers = []

    @classmethod
    def get_handlers(cls):
        handlers = cls.handlers
        handlers.extend( Config.instance().get_event_handlers(cls))
        return handlers

    @classmethod
    def emit(cls, *args, **kw):
        for handler in cls.get_handlers():
            handler(cls, *args, **kw)


class ContextChange(Event):
    handlers = [handlers.recheck_depedencies]

class FunctionExecuted(Event):
    pass

class ReplacementFunctionExecuted(FunctionExecuted):
    pass

class OriginalFunctionExecuted(FunctionExecuted):
    pass
