from .. import get_config
from .threadlocal import ThreadLocalMixin
from .objects import Logger

from IPython.lib import pretty

class Event:

    @classmethod
    def get_handlers(cls):
        return (cls.handle,)

    @classmethod
    def _get_handlers(cls):
        handlers = get_config().get_event_handlers(cls)
        if not handlers:
            handlers = cls.get_handlers()
        return handlers

    @classmethod
    def emit(cls, *args, **kw):
        for handler in cls._get_handlers():
            #if getattr(handler, 'pass_class', False):
            #    handler(cls, *args, **kw)
            #else:
            handler(*args, **kw)

    @classmethod
    def handle(cls, *args, **kw):
        pass


class LoggableEvent(Event):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    @classmethod
    def emit(cls, *args, **kw):
        event = cls(*args, **kw)
        super(LoggableEvent, cls).emit(event)

    @classmethod
    def get_handlers(cls):
        return (cls._log, cls.handle)

    def _log(self):
        logger = Logger.instance()
        self.index = len(logger)
        logger.append(self)

    def handle(self):
        'You can implement this.'

    def __repr__(self):
        return pretty.pretty(self)

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text('Event(...)')
            return
        with p.group(6, 'Event(', ')'):
            for idx, (attr, value) in enumerate(self.__dict__.items()):
                p.text('%s = %s,' % (attr, value))
                if idx + 1 != len(self.__dict__):
                    p.breakable()
