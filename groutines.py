# -*- coding: utf-8 -*-

from util import object_from_name

import wrapt
import greenlet
import types

from contextlib import contextmanager

class ExplicitNone(object): pass

class ForceReturn(object):
    def __init__(self, value):
        self.rv = value

class GreenWrapper(object):

    instances = {}

    def __new__(cls, target, *args, **kw):
        if target in cls.instances:
            return cls.instances[target]
        return super(GreenWrapper, cls).__new__(cls, target, *args, **kw)

    def __init__(self, target, listeners=set()):
        '''
        target is the method to patch (str)
        listeners are greenlets
        '''
        self.listeners = listeners
        if getattr(self, '_target', None):
            # already initialized
            return
        self._target_parent, self._target = object_from_name(target)
        self._target_attribute = target.split('.')[-1]
    
    @property
    def is_applied(self):
        return getattr(self._target_parent, self._target_attribute) != self._target
    
    def apply(self):
        setattr(self._target_parent, self._target_attribute, self(self._target))
    
    def restore(self):
        setattr(self._target_parent, self._target_attribute, self._target)
    
    @wrapt.function_wrapper
    def __call__(self, wrapped, instance, args, kwargs):
        enter_evt = FunctionCall('ENTER', wrapped, instance, args, kwargs)
        rv = None
        if wrapped.__name__ == 'pre_save':
            import ipdb; ipdb.set_trace()
        for gr in self.listeners:
            _rv = gr.switch(enter_evt)
            if isinstance(_rv, ForceReturn):
                return _rv
            elif _rv is not None:
                rv = _rv
        if rv is not None:
            return rv if rv is not ExplicitNone else None

        rv = wrapped(*args, **kwargs)
        
        exit_evt = FunctionCall('EXIT', wrapped, instance, args, kwargs, rv)
        for gr in self.listeners:
            _rv = gr.switch(exit_evt)
            if isinstance(_rv, ForceReturn):
                return _rv
            elif _rv is not None:
                rv = _rv
        return rv if rv is not ExplicitNone else None


class FunctionCall(object):
    '''
    An "event" meaning a callable that was listened to has been called.
    
    ``typ`` can be 'ENTER' or 'EXIT'.
    '''
    
    def __init__(self, typ, wrapped, instance, args, kwargs, rv=None):
        self.type = typ
        self._callabl = wrapped
        self._instance = instance
        self._args = args
        self.__dict__.update(kwargs)
        self.rv = rv
        self._greenlet = greenlet.getcurrent()

    def __iter__(self):
        if self._instance:
            args = (self._instance,) + self._args
        else:
            args = self._args
        return iter(args)
    
    def set_rv(self, value):
        ''
        self._greenlet.switch(value)
    
    def force_rv(self, value):
        self._greenlet.switch(ForceReturn(value))
    
    def return_None(self):
        self.set_rv(ExplicitNone)
        
@contextmanager
def wait_fcall(target, typ='EXIT', condition=None):
    g_self = greenlet.getcurrent()
    gwrapper = GreenWrapper(target, listeners=[g_self])
    if not gwrapper.is_applied:
        gwrapper.apply()

    while True:
        evt = g_self.parent.switch(None)
        if evt.type != typ:
            continue
        if condition and not condition(evt):
            continue
        yield evt
        break
    gwrapper.restore()


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
        with wait_fcall('__main__.SomeClass.middle') as evt:
            evt.set_rv(5)
    
    start_all([a_greenlet])
    
    o = SomeClass()
    print o.go()


    