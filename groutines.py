# -*- coding: utf-8 -*-

from util import object_from_name

import wrapt
import greenlet
import types
import ipdb

from contextlib import contextmanager

class ExplicitNone(object): pass

class ForceReturn(object):
    def __init__(self, value):
        self.rv = value

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
    
    @contextmanager
    def wait(self, condition=None):
        listener = Listener(condition)
        self.listeners.add(listener)
        yield greenlet.getcurrent().parent.switch(None)
        self.listeners.remove(listener)

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
    def is_applied(self):
        return getattr(self._target_parent, self._target_attribute) != self._target
    
    def apply(self):
        setattr(self._target_parent, self._target_attribute, self(self._target))
    
    def restore(self):
        setattr(self._target_parent, self._target_attribute, self._target)
    
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        all_args = (instance,) + args if instance else args
        enter_info = CallInfo(all_args,
                kwargs=dict(kwargs, type='ENTER', callable=wrapped))
        rv = None
        
        for listener in self.listeners:
            _rv = listener.send(enter_info)
            if isinstance(_rv, ForceReturn):
                return _rv
            elif _rv is not None:
                rv = _rv
        if rv is not None:
            return rv if rv is not ExplicitNone else None

        rv = wrapped(*args, **kwargs)
        
        exit_info = CallInfo(all_args,
                kwargs=dict(kwargs, type='EXIT', callable=wrapped, rv=rv))
        for listener in self.listeners:
            _rv = listener.send(exit_info)
            if isinstance(_rv, ForceReturn):
                return _rv
            elif _rv is not None:
                rv = _rv
        return rv if rv is not ExplicitNone else None

    @contextmanager
    def wait(self, typ='EXIT', condition=None):
        if not self.is_applied:
            self.apply()
        def _condition(evt):
            if evt.type != typ:
                return
            if condition and not condition(evt):
                return
            return True
        with super(FunctionCall, self).wait(_condition) as evt:
            yield evt
        if not self.listeners:
            self.restore()


class KwaTuple(tuple):
    '''
    Mutable tuple that is initialized from the dict of kwargs.
    '''
    
    def __new__(cls, *args, **kwargs):
        kwa = kwargs.pop('kwargs', {})
        obj = super(KwaTuple, cls).__new__(cls, *args, **kwargs)
        obj.__dict__.update(kwa)
        return obj


class CallInfo(KwaTuple):
    '''
    Info about a function call is a kwatuple (i.e. args + kwargs)
    + methods that allow to override function's return value.
    '''
    
    def __init__(self, *args, **kw):
        self._greenlet = greenlet.getcurrent()
    
    def set_rv(self, value):
        res =  self._greenlet.switch(value)
        return res
    
    def force_rv(self, value):
        return self._greenlet.switch(ForceReturn(value))
    
    def return_None(self):
        return self.set_rv(ExplicitNone)


class Listener(object):
    def __init__(self, condition=None):
        self.condition = condition
        self._greenlet = greenlet.getcurrent()
    
    def send(self, value):
        if self.condition and not self.condition(value):
            return
        return self._greenlet.switch(value)

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
    
    def a_greenlet(*args):
        with FunctionCall('__main__.SomeClass.middle').wait() as evt:
            evt.set_rv(10)
#    
#    with ipdb.launch_ipdb_on_exception():
    start_all([a_greenlet])
    
    o = SomeClass()
    print o.go()


    
