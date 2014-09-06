# -*- coding: utf-8 -*-

from . import Groutine, Event, make_event, DefaultFinder
import greenlet


class Scenario(Groutine):
    
    def __init__(self, scenario, args=(), kwargs={}, groutines=(),
                 discover=True, finder=DefaultFinder()):
        Groutine.__init__(self)
        self._scenario = scenario
        self.scenario_args = args
        self.scenario_kwargs = kwargs
        self._groutines = set(groutines)
        if discover:
            self._groutines |= set(finder.discover())
    
    def run(self, *args, **kwargs):
        self.groutines = []
        for func in self._groutines:
            gr = Groutine(func)
            self.groutines.append(gr)
            gr.switch()

        import time
        Event('SCENARIO_STARTED').fire(time.strftime('%x %X'))
        rv = self._scenario(*self.scenario_args, **self.scenario_kwargs)
        for gr in self.groutines:
            gr.throw()

        return rv


class InteractiveScenario(Scenario):
    '''
    Adds ability to interact with the "user".
    '''
    
    response = None
    
    def __init__(self, *args, **kwargs):
        Groutine.__init__(self)
        self.scenario = Scenario(*args, **kwargs)
        self.scenario.parent = self
        self.g_out = greenlet.getcurrent()
    
    def run(self, *args, **kw):
        if self.event != Event('SCENARIO_STARTED'):
            with Event('SCENARIO_STARTED').listen():
                self.scenario.switch()
        response = None
        
        while True:
            if self.scenario.dead:
                return value
            if not self.event:
                return self.scenario.switch()
            with self.event.listen(**self.listener_kwargs):
                value = self.scenario.switch(response)
            response = self.g_out.switch(value)
    
    def reply(self, value):
        self.response = value
    
    def wait(self, event=None, **listener_kwargs):
        if event and not isinstance(event, Event):
            event = make_event(event)
        self.event = event
        self.listener_kwargs = listener_kwargs
        
        response = self.response
        self.response = None
        return self.switch(response)

IScenario = InteractiveScenario

