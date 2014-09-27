
from .threadlocal import Config

class Event:

    @classmethod
    def get_handlers(cls):
        # take from class also
        return Config.instance().get_event_handlers(cls)

    @classmethod
    def emit(cls, value):
        for handler in cls.get_handlers():
            handler.handle(cls, value)


class ContextChange(Event):
    pass

class FunctionExecuted:
    pass

class ReplacementFunctionExecuted(FunctionExecuted):
    pass

class OriginalFunctionExecuted(FunctionExecuted):
    pass
