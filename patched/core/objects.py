from functools import reduce, partial
import os

from .threadlocal import ThreadLocalMixin

from ..util import pretty_custom, ObjectLookupPrinter

class Config(ThreadLocalMixin):
    '''
    The config threadlocal.
    '''

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
        from patched.patching.handlers import GlobalPatches
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

class Storage(ThreadLocalMixin):
    '''
    The storage threadlocal with a dict-like access.

    Elements should have dot-separated names, so that they could be
    organized into a tree:

        storage['core.objects'] = ['Logger', 'Storage', 'Config']
        storage['core.events'] = ['Event', 'LoggableEvent']

        >>> storage['core']
        {'objects': ['Logger', 'Storage', 'Config'],
         'events': ['Event', 'LoggableEvent']}
    '''

    global_name = 'storage'

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

class Logger(ThreadLocalMixin):
    '''
    The logger threadlocal. Consists of records which are lists of
    arbitrary objects.

    Objects in a record can override their default string representation
    with defined `_log_pretty_` method.
    '''
    global_name = 'logger'

    def __init__(self):
        self._list = []

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __contains__(self, item):
        return item in self._list

    def __getattr__(self, attr):
        return getattr(self._list, attr)

    def __getitem__(self, item):
        records = self._list[item]
        from .events import Event
        event, = (record for record in records if isinstance(record, Event))
        return event

    def _log_pretty_(self, p, cycle):
        if cycle:
            p.text('Logger(...)')
            return
        p.text('Logged events:')
        with p.group():
            for idx, line in enumerate(self):
                p.break_()
                start = '%d|' % idx
                with p.group(len(start), start):
                    for item in line:
                        p.breakable()
                        p.text( logpretty(item))

    def append(self, obj):
        '''Append obj to current record.'''
        assert len(self), "Empty log"
        self[-1].append(obj)

    def record(self, obj=None):
        '''Make new record and append obj (if any) to it.'''
        line = []
        if obj:
            line.append(obj)
        self._list.append(line)


    __repr__ = lambda self:  logpretty(self)

