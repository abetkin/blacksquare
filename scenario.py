# -*- coding: utf-8 -*-

from groutines import Groutine, switch
import greenlet
from dec import groutine, loop


class Scenario(Groutine):
    
    started = False
    
    def __init__(self, scenario, args=(), kwargs={}, groutines=()):
        greenlet.greenlet.__init__(self)
        self._scenario = scenario
        self.scenario_args = args
        self.scenario_kwargs = kwargs
        self._groutines = groutines
    
    def run(self, *args, **kwargs):
        self.started = True
        self.groutines = []
        for func in self._groutines:
            gr = Groutine(func)
            self.groutines.append(gr)
            gr.switch()
        rv = self._scenario(*self.scenario_args, **self.scenario_kwargs)
        for gr in self.groutines:
            gr.throw()
        return rv

from contextlib import contextmanager

class InteractiveScenario(Scenario):
    '''
    Adds ability to interact with the "user".
    '''
    
    response = None
    
    def __init__(self, scenario, args=(), kwargs={}, groutines=()):
        self.scenario = Scenario(scenario, args=args, kwargs=kwargs,
                                 groutines=groutines)
        greenlet.greenlet.__init__(self)
        self.g_out = self.parent
    
    def run(self, *args, **kw):
        
        @contextmanager
        def noop():
            yield
    
        while True:
            if self.event:
                lnr = self.event.listen(**self.listener_kwargs)
            else:
                lnr = noop()
            with lnr:
                if not self.scenario.started:
                    self.scenario.parent = self
                    value = self.scenario.switch()
                else:
                    value = switch(response)
            if self.scenario.dead:
                return value
            response = self.g_out.switch(value)
    
    def reply(self, value):
        self.response = value
    
    def wait(self, event=None, **listener_kwargs):
        self.event = event
        self.listener_kwargs = listener_kwargs
        
        response = self.response
        self.response = None
        self.switch(response)

IScenario = InteractiveScenario


if __name__ == '__main__':
    
    from groutines import FunctionCall, Event, ForceReturn
    
    class SomeClass(object):
            
        def __init__(self):
            self.a = 1
        
        def start(self):
            return 1
        
        @classmethod
        def middle(cls, default=2):
            return default
        
        def end(self):
            return 1
    
    
    @groutine.wrapper()
    def a_greenlet():
        print FunctionCall((SomeClass, 'middle'),
                           argnames=['default']
                           ).wait()
        for i in range(5):
            e = Event('OLD_VALUE')
            print e.fire(value=i)
        return ForceReturn(9)
        
    
    @loop.wrapper(Event('OLD_VALUE'))
    def big_value(value):
        return (value + 1)
        def sce():
            o = SomeClass()
            print SomeClass.middle(default=6)
    
    def sce():
        o = SomeClass()
        print SomeClass.middle(default=6)
        
    sc = IScenario(sce, groutines=[a_greenlet, big_value])
    sc.wait()
        