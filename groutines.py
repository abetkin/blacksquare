# -*- coding: utf-8 -*-

from util import object_from_name

import wrapt
import greenlet
import types
import itertools
from contextlib import contextmanager

import ipdb

from util import Counter

class ExplicitNone(object): pass

class ForceReturn(object):
    def __init__(self, value):
        self.value = value

'''
Since we presume our program single-threaded, ``switch_counter``
will tell us whether switch() was called in some piece of code or not.
'''
switch_counter = 0

def switch(*args, **kw):
    '''
    Switch to parent, a shortcut.
    '''
    global switch_counter
    switch_counter += 1
    return greenlet.getcurrent().parent.switch(*args, **kw)



class Listener(object):
    '''
    Listens to an event.
    '''
    ignore_exc = False
    
    def __init__(self, event, condition=None, grinlet=None):
        self.event = event
        self.condition = condition
        self._greenlet = grinlet or greenlet.getcurrent()
    
    # TODO: accept / throw
    def switch(self, value):
        if self.condition and not self.condition(value):
            return
        try:
            
            return self._greenlet.switch(value)
        except:
            if not self.ignore_exc: raise
        
        # TODO: process_exception

    def __enter__(self):
        self.event.listeners.add(self)
        return self
    
    def __exit__(self, *exc_info):
        print 'exit'
        self.event.listeners.remove(self)


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
        if not self.event.is_active:
            self.event.activate()
        return super(CallListener, self).__enter__()
    
    def __exit__(self, *exc_info):
        if not self.event.listeners:
            self.event.deactivate()
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
        return self.process_switches(_values())
    
    def process_switches(self, values_iter):
        '''
        Process values listeners switched back with.
        '''
        for value in values_iter:
            if value is not None: return value
    
    def wait(self, condition=None):
        with self.listener_class(self, condition):
            return switch()
        
#    def wait(self, condition=None):
#        listener = Listener(self, condition=)
#        self.listeners.add(listener)
#        evt = greenlet.getcurrent().parent.switch()
#        self.listeners.remove(listener)
#        return evt 


class FunctionCall(Event):
    '''
    A wrapper around a callable, allowing it to communicate with greenlets
    (listeners) subscribed to it.
    Event's name is callable's absolute import path (str).
    '''

    listener_class = CallListener

    def __init__(self, target):
        if target not in Event.instances:
            self._target_parent, self._target = object_from_name(target)
            self._target_attribute = target.split('.')[-1]
        super(FunctionCall, self).__init__(target)
    
    @property
    def is_active(self):
        return getattr(self._target_parent, self._target_attribute) != self._target
    
    def activate(self):
        '''
        Place wrapper instead of the target callable.
        '''
        setattr(self._target_parent, self._target_attribute, self(self._target)) 
    
    def deactivate(self):
        '''
        Put target callable on it's place back.
        '''
        setattr(self._target_parent, self._target_attribute, self._target)
    
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        all_args = (instance,) + args if instance else args
        enter_value = self.fire(all_args,
                **dict(kwargs, type='ENTER', callable=wrapped))
        if enter_value is not None:
            return enter_value if enter_value is not ExplicitNone else None

        rv = wrapped(*args, **kwargs)
        
        exit_value = self.fire(all_args,
                **dict(kwargs, type='EXIT', callable=wrapped, rv=rv))
        rv = exit_value or rv
        return rv if rv is not ExplicitNone else None

#    def wait(self, typ='EXIT', condition=None):
#        if not self.is_active:
#            self.activate()
#        def _condition(evt):
#            if evt.type != typ:
#                return
#            if condition and not condition(evt):
#                return
#            return True
#        evt = super(FunctionCall, self).wait(_condition)
#        if not self.listeners:
#            self.deactivate()
#        return evt

    def wait(self, typ='EXIT', condition=None):
        with self.listener_class(self, typ, condition):
            return switch()

    # XXX process_thrown_values ?
    def process_switches(self, values_iter):
        values = []
        for value in values_iter:
            if isinstance(value, ForceReturn):
                return value.value
            values.append(value)
        return super(FunctionCall, self).process_switches(values)


class Kwartuple(tuple):
    '''
    Tuple which initializes it's __dict__
    with keyword arguments passed to constructor.
    '''
    
    def __new__(cls, *args, **kwargs):
        obj = super(Kwartuple, cls).__new__(cls, *args)
        obj.__dict__.update(kwargs)
        return obj


def make_groutine(func):
    assert hasattr(func, '_groutine'), 'Groutine should be marked with a decorator'
    kwargs = func._groutine
    if kwargs['event']:
        should_stop = (itertools.count() if kwargs['once']
                       else itertools.repeat(0))
        def f():
            with kwargs['event'].listener_class(kwargs['event']):
                while not next(should_stop):
                    value = switch()
                    func(*value, **value.__dict__)
    else:
        f = func
    grinlet = greenlet.greenlet(f)
    grinlet.switch()
    return grinlet

    
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


#    @listener(FunctionCall('__main__.Counter'))
#    def patch(*args, **kwargs):
#        switch(10)

    from dec import groutine
    
    @groutine()
    def a_greenlet():
        evt = FunctionCall('__main__.Counter').wait()
        for i in range(5):
            Event('OLD_VALUE').fire(value=evt.rv)
        switch(ForceReturn(9))
        
        
#    @groutine()
#    def big_value():
#        evt = Event('OLD_VALUE').wait()
#        print evt.value
    
    @groutine(event=Event('OLD_VALUE'), once=False)
    def big_value(value):
        print '!', value
#    
#    with ipdb.launch_ipdb_on_exception():
    start_all([a_greenlet, big_value
                ])
    o = Counter()
    print o



    
