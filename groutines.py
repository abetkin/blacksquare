# -*- coding: utf-8 -*-

from util import object_from_name

import wrapt
import greenlet
import types
import ipdb

class ExplicitNone(object): pass

class ForceReturn(object):
    def __init__(self, value):
        self.value = value

def switch(*args, **kw):
    '''
    Switch to parent, a shortcut.
    '''
    return greenlet.getcurrent().parent.switch(*args, **kw)


class Event(object):
    '''
    An event is uniquely identified by it's name
    and has a set of listeners.
    '''
    instances = {}
    
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
        listener = Listener(condition)
        self.listeners.add(listener)
        evt = greenlet.getcurrent().parent.switch()
        self.listeners.remove(listener)
        return evt

class FunctionCall(Event):
    '''
    A wrapper around a callable, allowing it to communicate with greenlets
    (listeners) subscribed to it.
    Event's name is callable's absolute import path (str).
    '''

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

    def wait(self, typ='EXIT', condition=None):
        if not self.is_active:
            self.activate()
        def _condition(evt):
            if evt.type != typ:
                return
            if condition and not condition(evt):
                return
            return True
        evt = super(FunctionCall, self).wait(_condition)
        if not self.listeners:
            self.deactivate()
        return evt

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


class Listener(object):
    ignore_exc = False
    
    def __init__(self, condition=None):
        self.condition = condition
        self._greenlet = greenlet.getcurrent()
    
    def switch(self, value):
        if self.condition and not self.condition(value):
            return
        try:
            return self._greenlet.switch(value)
        except:
            if not self.ignore_exc: raise

def start_all(greenlets):
    for gr in greenlets:
        if type(gr) is types.FunctionType:
            gr = greenlet.greenlet(gr)
        gr.switch()


    
if __name__ == '__main__':
    
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

#    
    def a_greenlet(*args):
        print '!', args
        evt = FunctionCall('__main__.SomeClass.middle').wait()
        
        if evt.rv > 1:
            Event('OLD_VALUE').fire(value=evt.rv)
        switch(10)
#        switch(ForceReturn(9))
        
        
        
    def big_value(*args):
        evt = Event('OLD_VALUE').wait()
        print evt.value
#    
#    with ipdb.launch_ipdb_on_exception():
    start_all([a_greenlet, big_value
                ])
    
    o = SomeClass()
    print o.go()


    
