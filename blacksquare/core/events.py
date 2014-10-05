from ..config.core import Config

class Event:

    @classmethod
    def get_handlers(cls):
        return (cls,) #FIXME cls.handle

    @classmethod
    def _get_handlers(cls):
        handlers = Config.instance().get_event_handlers(cls)
        if not handlers:
            handlers = cls.get_handlers()
        return handlers

    @classmethod
    def emit(cls, *args, **kw):
        for handler in cls._get_handlers():
            #if getattr(handler, 'pass_class', False):
            #    handler(cls, *args, **kw)
            #else:
            handler.handle(*args, **kw)

    @classmethod
    def handle(cls, *args, **kw):
        pass

