import os

from ..config.core import Config
from .threadlocal import ThreadLocalMixin


class Event:
    #TODO: add thread locks for handling

    @classmethod
    def get_handlers(cls):
        return (cls.handle,)

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
            handler(*args, **kw)

    @classmethod
    def handle(cls, *args, **kw):
        pass

class Logger(ThreadLocalMixin, list):
    global_name = 'logger'

    def __str__(self):
        return os.linesep.join(str(record) for record in self)

    __repr__ = __str__


class LoggableEvent(Event):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    @classmethod
    def emit(cls, *args, **kw):
        event = cls(*args, **kw)
        super(LoggableEvent, cls).emit(event)

    @classmethod
    def get_handlers(cls):
        return (cls.handle, cls._log)

    def _log(self):
        Logger.instance().append(self)

    def handle(self):
        'You would want to implement this.'

    def __str__(self):
        # normally should be changed
        return ''.join((
            self.__class__.__name__,
            '(',
            ', '.join(("%s=%s" % item) for item in self.__dict__.items()),
            ')'
        ))
