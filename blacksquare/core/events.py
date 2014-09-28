from ..config.core import Config

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
            if getattr(handler, 'pass_class', False):
                handler(cls, *args, **kw)
            else:
                handler(*args, **kw)
