# -*- coding: utf-8 -*-

'''
Here live decorators and related stuff
'''


from . import Groutine, make_event, Event

class GroutineFunction(object):
    '''
    Wraps functions supposed to be groutines.
    '''
    def __init__(self, function, event=None, **listener_kwargs):
        self.function = function
        if event and not isinstance(event, Event):
            event = make_event(event)
        self.event = event
        self.listener_kwargs = listener_kwargs
        self.__name__ = self.function.__name__
    
    @classmethod
    def wrapper(cls, *args, **kwargs):
        return lambda func: cls(func, *args, **kwargs)  
    
    def __repr__(self):
        return '%s groutine function' % self.function.__name__
    
    def __call__(self):
        if not self.event:
            return self.function()
        with self.event.listen(**self.listener_kwargs) as lnr:
            value = lnr.send()
        rv = self.function(**value)
        lnr.send(rv)

groutine = GroutineFunction.wrapper

class Loop(GroutineFunction):
    
    def __call__(self):
        with self.event.listen(**self.listener_kwargs) as lnr:
            value = lnr.send() 
            while True:
                rv = self.function(**value)
                value = lnr.send(rv)

loop = Loop.wrapper

if __name__ == '__main__':
    @groutine()
    def f():
        return 1
    f = Groutine(f)
    print (f.switch())
    
    