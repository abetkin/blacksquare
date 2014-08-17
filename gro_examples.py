# -*- coding: utf-8 -*-

from groutines import FCall, switch, ForceReturn, Event
from dec import groutine, loop

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
        

def scenario():
    o = SomeClass()
    print SomeClass.middle(default=6)


@groutine.wrapper()
def a_greenlet():
    print FCall((SomeClass, 'middle'),
                       argnames=['default']
                       ).wait()
    for i in range(5):
        e = Event('OLD_VALUE')
        print e.fire(value=i)
    return ForceReturn(9)
    

@loop.wrapper(Event('OLD_VALUE'))
def big_value(value):
    return (value + 1)

if __name__ == '__main__':
    
    from scenario import IScenario
    
    sc = IScenario(scenario, groutines=(a_greenlet, big_value), discover=0
            )
    sc.wait()