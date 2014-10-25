from functools import reduce, partial
import os

from .threadlocal import ThreadLocalMixin

from ..util import pretty_custom, ObjectLookupPrinter

class Config(ThreadLocalMixin):

    global_name = "config"

    def __init__(self):
        # maybe read from somewhere
        self._event_handlers = {}
        self.breakpoints = set()

    def get_event_handlers(self, event_cls):
        return self._event_handlers.get(event_cls, ())

    def register_event_handler(self, event_cls, handler):
        self._event_handlers.setdefault(event_cls, []).append(handler)

    def unregister_event_handler(self, event_cls, handler):
        handlers = self._event_handlers[event_cls]
        handlers.remove(handler)

    def get_controller_class(self):
        from blacksquare.patching.handlers import GlobalPatches
        return GlobalPatches

    def set_breakpoint(self, index):
        self.breakpoints.add(index)

    def unset_breakpoint(self, index):
        self.breakpoints.discard(index)

    debugger = 'ipdb'
    fake_interactive_shell = None


class DictAndObject(dict):
    def __init__(self, *args, **kw):
        super(DictAndObject, self).__init__(*args, **kw)
        self.__dict__ = self

class ContextTree(ThreadLocalMixin):

    global_name = 'context'

    def __init__(self):
        self._dict = DictAndObject()

    def __setitem__(self, name, value):
        from ..patching.events import ContextChange
        ContextChange.emit(name)

        path = name.split('.')
        last_part = path.pop()
        obj = self._dict
        for part in path:
            obj = obj.setdefault(part, DictAndObject())
        obj[last_part] = value

    def __getitem__(self, name):
        path = name.split('.')
        return reduce(lambda x,y: x[y], path, self._dict)


class LogPrinter(ObjectLookupPrinter):
    lookup_attribute = '_log_pretty_'

logpretty = partial(pretty_custom, printer_class=LogPrinter)

class Logger(ThreadLocalMixin, list):
    global_name = 'logger'

    def _log_pretty_(self, p, cycle):
        if cycle:
            p.text('Logger(...)')
            return
        p.text('Logged events:')
        if self:
            p.break_()
        with p.group():
            for idx, item in enumerate(self):
                p.text('%d| ' % idx)
                p.pretty(item)
                if idx != len(self) - 1:
                    p.break_()

    #def _repr_pretty_(self, p, cycle):
    #    p.text( logpretty(self))

    __repr__ = lambda self:  logpretty(self)

