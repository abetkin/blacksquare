# -*- coding: utf-8 -*-

from groutines import Groutine, switch
import greenlet
from discovery import DefaultFinder


class Scenario(Groutine):
    
    started = False
    
    def __init__(self, scenario, args=(), kwargs={}, groutines=(),
                 discover=True, finder=DefaultFinder()):
        greenlet.greenlet.__init__(self)
        self._scenario = scenario
        self.scenario_args = args
        self.scenario_kwargs = kwargs
        self._groutines = set(groutines)
        if discover:
            self._groutines &= set(finder.discover())
    
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
    
    def __init__(self, *args, **kwargs):
        greenlet.greenlet.__init__(self)
        self.scenario = Scenario(*args, **kwargs)
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
    
    1