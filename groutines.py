# -*- coding: utf-8 -*-

from util import object_from_name

import wrapt
import greenlet
import types
import itertools
from contextlib import contextmanager
import collections

import ipdb

from util import Counter

class ExplicitNone(object): pass

class ForceReturn(object):
    def __init__(self, value):
        self.value = value

def switch(value=None):
    '''
    Global function: switch values with parent greenlet.
    '''
    rv = greenlet.getcurrent().parent.switch(value)
    
    # since it's global function and
    # we presume our programs single-threaded
    # logging swiches may be helpful.
    switch_logger.add(value, rv)
    return rv


class Listener(object):
    '''
    Listens to an event.
    '''
    
    def __init__(self, event, condition=None, grinlet=None):
        self.event = event
        self.condition = condition
        self._greenlet = grinlet or greenlet.getcurrent()
    
    def switch(self, value):
        if self.condition and not self.condition(value):
            return
        try:
            return self._greenlet.switch(value)
        except Exception as exc:
            self.handle_exception(exc)
        
    def handle_exception(self, exc):
        raise exc

    def __enter__(self):
        self.event.listeners.add(self)
        return self
    
    def __exit__(self, *exc_info):
        self.event.listeners.remove(self)
    
    __str__ = __repr__ = lambda self: 'listener: %s' % self.event.name


class CallListener(Listener):
    
    def __init__(self, event, typ='EXIT', condition=None, grinlet=None):
        
        def _condition(value):
            if value.type != typ:
                return
            if condition and not condition(value):
                return
            return True

        super(CallListener, self).__init__(event, _condition, grinlet) 
    
    def __enter__(self):
        if not self.event.callable_wrapper.patched:
            self.event.callable_wrapper.patch()
        return super(CallListener, self).__enter__()
    
    def __exit__(self, *exc_info):
        if not self.event.listeners:
            self.event.callable_wrapper.restore()
        super(CallListener, self).__exit__(*exc_info)


class Event(object):
    '''
    An event is uniquely identified by it's name
    and has a set of listeners.
    '''
    instances = {}
    listener_class = Listener
    
    def __new__(cls, name, *args, **kw):
        if name in Event.instances:
            return Event.instances[name]
        return super(Event, cls).__new__(cls, name, *args, **kw)

    def __init__(self, name):
        if name in Event.instances:
            return
        self.name = name
        self.listeners = set()
        Event.instances[name] = self
    
    def fire(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], Kwartuple):
            value = args[0]
        else:
            value = Kwartuple(args, **kwargs)
            
        def _values():
            for listener in tuple(self.listeners):
                listener._greenlet.parent = greenlet.getcurrent()
                yield listener.switch(value)
        return self.process_responses(_values())
    
    def process_responses(self, values_iter):
        '''
        Process values listeners switch back with
        in response to fired events.
        '''
        for value in values_iter:
            if value is not None: return value
    
    def listen(self, *args, **kwargs):
        '''
        Create a listener. 
        '''
        return self.listener_class(self, *args, **kwargs)
    
    def wait(self, *listener_args, **listener_kwargs):
        '''
        Shortcut. Listens only until the first firing of the event.
        
        Makes values switch with the listener groutine.
        '''
        with self.listen(*listener_args, **listener_kwargs):
            return switch()


class CallableWrapper(object):
    '''
    Wraps a callable. Calls respective events (``event``) before and after
    the target call. Events sent differ in ``type`` argument:
    'ENTER' and 'EXIT' respectively.

    '''
    
    def __init__(self, event, target):
        self.event = event
        self._target_parent, self._target = object_from_name(target)
        self._target_attribute = target.split('.')[-1]
        self.patched = False


    def patch(self):
        '''
        Replace original with wrapper.
        '''
        setattr(self._target_parent, self._target_attribute, self(self._target))
        self.patched = True
    
    def restore(self):
        '''
        Put original callable on it's place back.
        '''
        setattr(self._target_parent, self._target_attribute, self._target)
        self.patched = False
        
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        all_args = (instance,) + args if instance else args
        enter_value = self.event.fire(*all_args,
                **dict(kwargs, type='ENTER', callable=wrapped))
        if enter_value is not None:
            return enter_value if enter_value is not ExplicitNone else None

        rv = wrapped(*args, **kwargs)
        
        exit_value = self.event.fire(*all_args,
                **dict(kwargs, type='EXIT', callable=wrapped, rv=rv))
        rv = exit_value or rv
        return rv if rv is not ExplicitNone else None



class FunctionCall(Event):
    '''
    Is fired when target callable is called (event's name is callable's
    import path).
    
    ``callable_wrapper`` is responsible for the respective patching.
    '''

    listener_class = CallListener

    def __init__(self, name):
        if name not in Event.instances:
            self.callable_wrapper = CallableWrapper(self, name)
        super(FunctionCall, self).__init__(name)

    def process_responses(self, values_iter):
        values = []
        for value in values_iter:
            if isinstance(value, ForceReturn):
                return value.value
            values.append(value)
        return super(FunctionCall, self).process_responses(values)


class Kwartuple(tuple):
    '''
    Tuple which initializes it's __dict__
    with keyword arguments passed to constructor.
    '''
    
    def __new__(cls, *args, **kwargs):
#        ipdb.set_trace()
        obj = super(Kwartuple, cls).__new__(cls, *args)
        obj.__dict__.update(kwargs)
        return obj


def make_groutine(func):
    # XXX: refactor to class?
    assert hasattr(func, '_groutine'), 'Groutine should be marked with a decorator'
    kwargs = func._groutine
    if not kwargs['event']:
        f = func
    else:
        event = kwargs['event']
        if not isinstance(event, Event):
            # saves typing, but probably too unrestrictive
            event = Event(event)
        
        listener_kwargs = kwargs['listener_kwargs']
        should_stop = (itertools.count() if kwargs['once']
                       else itertools.repeat(0))
        def f():
            with event.listen(**listener_kwargs):
                value = switch()
                while not next(should_stop):
                    P = switch_logger.count
                    func(*value, **value.__dict__)
                    if switch_logger.count > P:
                        value = switch_logger[-1][1] # last logged value
                    elif not kwargs['once']:
                        value = switch()

    grinlet = greenlet.greenlet(f)
    grinlet.switch() # ignore switched value
    return grinlet


class SwitchLogger(object):
    
    def __init__(self, maxlen=10):
        self.deque = collections.deque(maxlen=maxlen)
        self._counter = itertools.count()
        self.count = next(self._counter)
    
    def add(self, forth, back):
        self.deque.append((forth, back))
        self.count = next(self._counter)
    
    def __getitem__(self,key):
        return self.deque[key]

switch_logger = SwitchLogger(100)

    
if __name__ == '__main__':
    
    def start_all(funcs):
        for f in funcs:
            make_groutine(f)
    
    class SomeClass(object):
        
        def __init__(self):
            self.a = 1
        
        def start(self):
            return 1
        
        def middle(self):
            return 2
        
        def end(self):
            return 1
        
        def go(self):
            for value in self.start(), self.middle(), self.end():
                self.a += value
            return self.a


    from dec import groutine
    
    @groutine()
    def a_greenlet():
        evt = FunctionCall('__main__.Counter').wait()
        for i in range(5):
            e = Event('OLD_VALUE')
            val = e.fire(value=i)
        switch(ForceReturn(9))
        
        
#    @groutine()
#    def big_value():
#        evt = Event('OLD_VALUE').wait()
#        print evt.value
    
    @groutine(event=Event('OLD_VALUE'), once=False)
    def big_value(value):
#        switch(value + 1)
        print(value + 1)
#    
#    with ipdb.launch_ipdb_on_exception():
    start_all([a_greenlet, big_value
                ])
    o = Counter()
#    for i in switch_logger.deque: print i
    
#%%
#def f(*args)
#%%



    
