# -*- coding: utf-8 -*-

from groutines import Groutine, Loop, FCall, switch, ForceReturn, Event, main

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

@Groutine()
def a_greenlet():
    val = FCall((SomeClass, 'middle'),
                       argnames=['default']
                       ).wait()
#        from pdb import Pdb
#        Pdb().set_trace(groutines_all['big_value'].gr_frame)
    print val
#        evt = FunctionCall('__main__.SomeClass.middle').wait()
    for i in range(5):
        e = Event('OLD_VALUE')
        print e.fire(value=i)
    switch(ForceReturn(9))
        
        
#    @groutine()
#    def big_value():
#        evt = Event('OLD_VALUE').wait()
#        print evt.value
    
@Loop(Event('OLD_VALUE'))
def big_value(value):
    return (value + 1)
    


if __name__ == '__main__':
    main(scenario)